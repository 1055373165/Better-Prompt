# Go 调度器是怎么把 Goroutine 换下来的：抢占、系统调用与唤醒

> 接续上一篇对 `runtime.rt0_go`、主 goroutine 创建和核心调度循环的分析。本文继续往下看：一个 goroutine 没有在当前调度周期内跑完时，Go runtime 究竟是怎么把它换下来的。

## 1. 写在前面

上一篇文章主要解决了一个问题：**Go 程序是怎么从二进制入口一路走到 `main.main` 的。**

但真正理解调度器，光看到 `schedule -> findRunnable -> execute -> gogo` 这条链还不够。更关键的问题其实在后面：

1. 一个 goroutine 正常执行完之后，runtime 怎么收尾？
2. 一个 goroutine 跑太久了，调度器怎么把它换下去？
3. 如果它一直不做函数调用，协作式抢占失效了怎么办？
4. 如果它陷入系统调用，M、P、G 三者的关系又会怎么变化？
5. 一个休眠的 M，是怎么再次被唤醒并回到工作循环的？

这些时刻，才是 Go 调度器真正体现工程细节的地方。

本文默认基于 `Go 1.23` 来讨论 goroutine 调度逻辑，主体仍按 `linux/arm64` 的 runtime 设计理解。少量系统调用包装代码在不同平台上的实现细节会有差异，但本文关心的是 runtime 的共性结构：**保存现场、切换状态、解绑/重绑 MP、重新进入调度循环。**

## 2. 先给全景图

如果只保留最重要的结论，那么一个 goroutine 离开 CPU，大致只有下面几条路径：

1. **正常执行完成**
   目标函数返回，跳到 `goexit`，切回 `g0`，清理资源，再次进入 `schedule`。
2. **协作式抢占**
   `sysmon` 发现某个 G 运行太久，给它打上抢占标记；G 在下一次函数调用的序言里发现标记，主动让出 M。
3. **异步信号抢占**
   如果 G 长时间不发生函数调用，协作式抢占失效，runtime 就向对应 M 发送抢占信号，强行把执行流劫持到 `asyncPreempt`。
4. **陷入系统调用**
   进入内核前，runtime 先把 G 标成 `_Gsyscall`，把 P 从 M 上解绑；系统调用返回后，再尝试重新拿回 P，继续执行或回到队列。
5. **主动阻塞**
   比如 channel、mutex、timer、network poll 等待，本质上也都是把当前 G 从运行态切到某种等待态，然后让 M 继续找下一个 G。

本文重点看前四种。

## 3. 先从最简单的情况开始：goroutine 正常执行完成

上一篇文章里提到过，goroutine 在创建时，runtime 会提前给它伪造一个 `goexit` 返回地址。

也就是说，goroutine 绑定的目标函数执行完以后，并不是“自然消失”，而是会回到 runtime 预先准备好的收尾路径。

先看这条路径的骨架：

```asm
TEXT runtime.goexit(SB), NOSPLIT|NOFRAME|TOPFRAME,$0-0
	MOVD R0, R0
	BL runtime.goexit1(SB)
```

继续往下：

```go
func goexit1() {
	...
	mcall(goexit0)
}
```

再往下：

```go
func goexit0(gp *g) {
	gdestroy(gp)
	schedule()
}
```

这几段代码串起来，逻辑非常清楚：

1. goroutine 目标函数执行完。
2. `RET` 弹出返回地址，跳到 `goexit`。
3. `goexit1` 调用 `mcall(goexit0)`。
4. `mcall` 切到当前 M 的 `g0` 栈。
5. `goexit0` 清理 goroutine 资源，再次进入 `schedule`。

这里最关键的是 `mcall`。它的职责不是“普通函数调用”，而是：

1. 保存当前 G 的执行现场。
2. 把当前 M 的栈从用户 G 的栈切到 `g0` 栈。
3. 在 `g0` 栈上执行运行时代码。

为什么清理动作一定要在 `g0` 上做？原因也不复杂：**goroutine 的栈本身就是待回收对象，不能站在自己的栈上做栈回收。**

所以，正常执行完成这条路径，本质上是：

`用户函数返回 -> goexit -> mcall -> g0 -> gdestroy -> schedule`

这是后面所有“离开 CPU”路径里最基础的一条。

## 4. 一条 goroutine 没跑完：协作式抢占

正常返回只是最简单的情况。更常见的情况是：一个 goroutine 在当前调度周期内没有执行完成。

这时候 runtime 要做的事情不是“杀掉它”，而是让它暂时让出 M，把 CPU 时间分给别的 G。

### 4.1 `sysmon` 在看什么

这一步的源头是 `sysmon`。

`sysmon` 不需要绑定 P，它是 Go runtime 的后台监控线程，主要做两类事：

1. 定期做 netpoll，避免网络事件长时间得不到处理。
2. 检查运行过久的 G，以及长时间停在系统调用里的 P。

和抢占相关的关键逻辑在 `retake`：

```go
func retake(now uint64) uint32 {
	...
	for i := 0; i < len(allp); i++ {
		pp := allp[i]
		...
		s := pp.status
		if s == _Prunning || s == _Psyscall {
			t := int64(pp.sysmontick.schedtick)
			...
			if pd.schedwhen+forcePreemptNS <= now {
				preemptone(pp)
			}
		}
		...
	}
}
```

这段逻辑的核心判断是：

1. 某个 P 上的调度周期长时间没有变化。
2. 说明当前正在运行的 G 占用了过长时间。
3. 到了阈值后，调用 `preemptone(pp)` 发起抢占。

### 4.2 `preemptone` 做了什么

`preemptone` 先走的是协作式路径：

```go
func preemptone(pp *p) bool {
	mp := pp.m.ptr()
	if mp == nil || mp == getg().m {
		return false
	}
	gp := mp.curg
	if gp == nil || gp == mp.g0 {
		return false
	}

	gp.preempt = true
	gp.stackguard0 = stackPreempt

	if preemptMSupported && debug.asyncpreemptoff == 0 {
		pp.preempt = true
		preemptM(mp)
	}
	return true
}
```

先只看协作式部分：

1. 把 `gp.preempt` 设为 `true`。
2. 把 `gp.stackguard0` 改成 `stackPreempt`。

这两个标记的作用分别是：

1. `preempt` 表示“这个 G 已经被请求抢占”。
2. `stackguard0 = stackPreempt` 则是为了让它在下一次函数调用时，经过函数序言检查时发现异常。

### 4.3 为什么“函数调用”会成为协作式抢占的切入点

Go 编译器会在函数入口插入一小段序言代码，用来检查栈空间是否够用。

正常情况下，这段代码是在检查：

1. 当前栈指针是否越过 `stackguard0`
2. 如果越过，就触发扩栈

而在协作式抢占场景里，runtime 故意把 `stackguard0` 改成非法值 `stackPreempt`。这样一来，goroutine 下一次进入函数调用时，就会把这次检查识别成“不是普通扩栈，而是该让出执行权了”。

也就是说，协作式抢占依赖的是一句很朴素的前提：

> 只要这个 goroutine 还会继续做函数调用，runtime 就总能找到机会把它拦下来。

### 4.4 主动让出 M 的真正落点

当 goroutine 在函数序言里发现自己被打了抢占标记，它最终会走到让出执行权的逻辑，比如 `Gosched` 或其底层实现。

对 runtime 来说，抢占的结果并不复杂：

1. 把当前 G 的现场保存起来。
2. 把它的状态从 `_Grunning` 改成 `_Grunnable`。
3. 把它重新放回运行队列。
4. 让 M 回到 `schedule`，去执行别的 G。

如果只看调度器视角，这一步和“这个 G 暂停一下，稍后再来”没有本质区别。

### 4.5 协作式抢占的边界

协作式抢占有一个明显前提：**G 必须再次进入某个函数调用点。**

如果 goroutine 在执行一个长时间的纯计算循环，而且循环体里没有函数调用，那么它就不会触发函数序言，也就不会主动让出 M。

这就是异步信号抢占存在的原因。

## 5. 协作式不够时，runtime 怎么强行抢占：异步信号抢占

Go 1.14 之后，runtime 增加了基于信号的异步抢占机制，用来覆盖“长时间不做函数调用”的场景。

### 5.1 从 `preemptM` 开始

前面看过，`preemptone` 在设置完协作式标记之后，还会进一步调用：

```go
if preemptMSupported && debug.asyncpreemptoff == 0 {
	pp.preempt = true
	preemptM(mp)
}
```

继续往下：

```go
func preemptM(mp *m) {
	if mp.signalPending.CompareAndSwap(0, 1) {
		signalM(mp, sigPreempt)
	}
}
```

这里做的事很直接：向目标 M 对应的系统线程发送 `sigPreempt`。

底层实现通常类似：

```go
func signalM(mp *m, sig int) {
	pthread_kill(pthread(mp.procid), uint32(sig))
}
```

也就是说，runtime 现在不是“等 G 自己路过检查点”，而是直接去打断这个线程当前的执行流。

### 5.2 信号最终会落到 `sighandler`

在 M0 启动阶段，runtime 已经把一系列信号处理函数安装好了。抢占信号到达后，会走到 `sighandler`：

```go
func sighandler(sig uint32, info *siginfo, ctxt unsafe.Pointer, gp *g) {
	gsignal := getg()
	mp := gsignal.m
	c := &sigctxt{info, ctxt}

	if sig == _SIGPROF {
		sigprof(c.sigpc(), c.sigsp(), c.siglr(), gp, mp)
		return
	}

	if sig == sigPreempt && debug.asyncpreemptoff == 0 && !delayedSignal {
		doSigPreempt(gp, c)
	}
	...
}
```

这里要注意两点：

1. 信号处理程序本身跑在 `gsignal` 的信号栈上。
2. 参数里的 `gp` 才是信号到来时，那个真正正在执行的用户 goroutine。

抢占逻辑真正的关键点在 `doSigPreempt`。

### 5.3 `doSigPreempt` 并不直接调度，它只是“改现场”

看核心代码：

```go
func doSigPreempt(gp *g, ctxt *sigctxt) {
	if wantAsyncPreempt(gp) {
		if ok, newpc := isAsyncSafePoint(gp, ctxt.sigpc(), ctxt.sigsp(), ctxt.siglr()); ok {
			ctxt.pushCall(abi.FuncPCABI0(asyncPreempt), newpc)
		}
	}

	gp.m.preemptGen.Add(1)
	gp.m.signalPending.Store(0)
}
```

这段代码最重要的一步是：

```go
ctxt.pushCall(abi.FuncPCABI0(asyncPreempt), newpc)
```

它不是直接把当前 G 放回队列，而是修改信号返回时将要恢复的 CPU 上下文。换句话说：

**当信号处理函数结束以后，这个 goroutine 不会回到原来那条指令继续跑，而是会先跳到 `asyncPreempt`。**

### 5.4 `pushCall` 的本质：伪造一个函数调用

`pushCall` 做的事情，可以概括成一句话：

> 在当前被打断 goroutine 的栈和寄存器现场上，硬塞进去一个对 `asyncPreempt` 的调用。

伪代码大致如下：

```go
func (c *sigctxt) pushCall(targetPC, resumePC uintptr) {
	sp := c.sp() - 16
	c.set_sp(sp)

	*(*uint64)(unsafe.Pointer(uintptr(sp))) = c.lr()
	*(*uint64)(unsafe.Pointer(uintptr(sp - goarch.PtrSize))) = c.r29()

	c.set_lr(uint64(resumePC))
	c.set_pc(uint64(targetPC))
}
```

逻辑很清楚：

1. 先在栈上腾出空间。
2. 保存原来的返回地址和帧指针。
3. 把 `PC` 改成 `asyncPreempt`。
4. 把它“返回以后该去哪儿”设置成原来被中断的位置。

所以异步抢占并不神秘，它本质上就是：**利用信号中断修改 goroutine 现场，再伪造一层函数调用，把执行流导向 runtime 的抢占入口。**

### 5.5 `asyncPreempt` 最终还是会回到 `mcall`

`asyncPreempt` 是一段汇编函数，它会保存大量寄存器，随后调用 `asyncPreempt2`：

```go
func asyncPreempt2() {
	gp := getg()
	gp.asyncSafePoint = true

	if gp.preemptStop {
		mcall(preemptPark)
	} else {
		mcall(gopreempt_m)
	}
	gp.asyncSafePoint = false
}
```

注意这里又出现了熟悉的 `mcall`。也就是说，异步抢占和 goroutine 正常退出一样，最终还是会先切回 `g0` 栈，再由 runtime 完成后续调度动作。

继续往下：

```go
func gopreempt_m(gp *g) {
	goschedImpl(gp, true)
}
```

再看 `goschedImpl` 的骨架：

```go
func goschedImpl(gp *g, preempted bool) {
	casgstatus(gp, _Grunning, _Grunnable)
	dropg()
	lock(&sched.lock)
	globrunqput(gp)
	unlock(&sched.lock)

	if mainStarted {
		wakep()
	}
	schedule()
}
```

这一步的结果就是：

1. 当前长时间运行的 G 被从 `_Grunning` 改成 `_Grunnable`。
2. 它被放进全局运行队列。
3. 当前 M 与 G 解绑。
4. M 回到 `schedule()`，继续调度其他 goroutine。

从调度器视角看，异步抢占的终点并不复杂：**把这个占用过久的 G 赶回队列，然后继续工作。**

### 5.6 协作式和异步抢占的分工

这两种机制不是互斥的，而是分层配合：

1. **优先协作式抢占**
   成本低，路径短，只要 G 还会走到函数调用点，优先走这条。
2. **协作式失效时才走异步信号抢占**
   成本更高，也更复杂，但能覆盖“纯计算死循环”这类场景。

所以更准确的说法不是“Go 用协程调度”，而是：

> Go 运行时同时具备协作式和异步抢占能力，并按成本由低到高逐级介入。

## 6. Goroutine 陷入系统调用时，G、M、P 怎么变化

抢占解决的是“G 一直占着 M 不放”的问题。系统调用场景则更麻烦：**M 这次不是忙，而是可能真的要进内核阻塞。**

如果这时候还让它一直占着 P，那 P 本地队列上的其他 G 就会一起被拖住。

这也是为什么 Go 在系统调用前后，要做一套专门的“解绑/重绑”流程。

### 6.1 先看三明治结构

以文件打开或其他普通阻塞系统调用为例，Go runtime 包装后的结构通常都可以抽象成这样：

```go
entersyscall()
// 真正的 syscall / libc call / 内核调用
exitsyscall()
```

Linux 下经常能直接在汇编里看到类似结构：

```asm
TEXT ·SyscallNoError(SB),NOSPLIT,$0-48
	BL	runtime·entersyscall(SB)
	...
	SVC
	...
	BL	runtime·exitsyscall(SB)
	RET
```

不同平台中间那层“真正发起系统调用”的包装会不一样：有的平台偏汇编直达，有的平台会经过 libc 包装。但对 runtime 来说，最关键的始终是上下两层“面包片”：

1. `entersyscall`
2. `exitsyscall`

### 6.2 `entersyscall`：先把现场收干净

进入系统调用前，runtime 要先做几件事：

1. 保存当前 G 的 `pc/sp/bp`。
2. 把 G 的状态从 `_Grunning` 改成 `_Gsyscall`。
3. 把当前 M 和 P 解绑。
4. 把 P 的状态改成 `_Psyscall`，让 `sysmon` 知道这个 P 可能需要被接管。

骨架代码大致如下：

```go
func entersyscall() {
	fp := getcallerfp()
	reentersyscall(getcallerpc(), getcallersp(), fp)
}

func reentersyscall(pc, sp, bp uintptr) {
	gp := getg()

	gp.m.locks++
	gp.stackguard0 = stackPreempt
	gp.throwsplit = true

	save(pc, sp, bp)
	gp.syscallsp = sp
	gp.syscallpc = pc
	gp.syscallbp = bp

	casgstatus(gp, _Grunning, _Gsyscall)

	pp := gp.m.p.ptr()
	pp.m = 0
	gp.m.oldp.set(pp)
	gp.m.p = 0
	atomic.Store(&pp.status, _Psyscall)

	gp.m.locks--
}
```

这一段最值得记住的，不是每个字段名，而是状态变化：

1. `G: _Grunning -> _Gsyscall`
2. `M.p = nil`
3. `M.oldp = 原来的 P`
4. `P: _Prunning -> _Psyscall`

也就是说，**系统调用一旦开始，Go runtime 就先默认这个 M 可能会长时间不可用，于是把 P 从它手里拿出来，留给后续调度。**

### 6.3 为什么 runtime 要保存 `oldp`

注意这里有一个细节：M 虽然和 P 解除了绑定，但 `gp.m.oldp` 还保留着之前那个 P。

这是为了给 `exitsyscall` 提供一条快速返回路径：

1. 如果系统调用很快返回，而且原来的 P 还在 `_Psyscall` 状态没人抢走；
2. 那当前 M 就可以优先把这个 P 拿回来，直接继续执行。

这个设计背后的考虑很现实：**优先复用原来的 P，局部性更好，代价也更低。**

### 6.4 系统调用期间，`sysmon` 会不会把这个 P 拿走

会，而且这正是 handoff 机制存在的原因。

`sysmon` 在 `retake` 里除了检查长时间运行的 G，也会检查 `_Psyscall` 状态的 P：

```go
if s == _Psyscall {
	...
	if runqempty(pp) && sched.nmspinning.Load()+sched.npidle.Load() > 0 && pd.syscallwhen+10*1000*1000 > now {
		continue
	}
	...
	if atomic.Cas(&pp.status, s, _Pidle) {
		pp.syscalltick++
		handoffp(pp)
	}
}
```

这段逻辑的核心意思是：

1. 如果一个 P 在系统调用里待得足够久；
2. 并且回收它确实有意义；
3. 那么 `sysmon` 会把它从 `_Psyscall` 改成 `_Pidle`；
4. 再调用 `handoffp(pp)`，把它交给别的 M 去用。

### 6.5 `handoffp` 的原则其实很简单

`handoffp` 并不是神秘逻辑，它的核心原则可以概括成一句话：

> 只要这个 P 上还有理由继续工作，就应该尽快给它配一个 M。

常见判断大致包括：

1. 本地或全局队列里有可运行的 G。
2. 有 GC worker、trace reader 等特殊工作。
3. 当前没有自旋 M，需要补一个自旋 M 去找活。
4. 边界情况下需要及时做 netpoll。

如果都不满足，P 才真正回到空闲列表。

从运行时角度看，这一步的意义很明确：**不要让一个被系统调用卡住的 M，顺手把它手上的 P 也一起拖死。**

### 6.6 系统调用返回以后，先走 `exitsyscall`

系统调用从内核返回后，执行流最终会走到 `exitsyscall`：

```go
func exitsyscall() {
	gp := getg()
	...
	oldp := gp.m.oldp.ptr()
	gp.m.oldp = 0

	if exitsyscallfast(oldp) {
		casgstatus(gp, _Gsyscall, _Grunning)
		return
	}

	gp.m.locks--
	mcall(exitsyscall0)
}
```

这里有两条路径：

1. 快速路径：`exitsyscallfast`
2. 慢速路径：`mcall(exitsyscall0)`

### 6.7 快速路径：优先尝试把 P 直接拿回来

`exitsyscallfast` 的策略很简单：

```go
func exitsyscallfast(oldp *p) bool {
	if oldp != nil && oldp.status == _Psyscall &&
		atomic.Cas(&oldp.status, _Psyscall, _Pidle) {
		wirep(oldp)
		return true
	}

	if sched.pidle != 0 {
		var ok bool
		systemstack(func() {
			ok = exitsyscallfast_pidle()
		})
		if ok {
			return true
		}
	}
	return false
}
```

顺序是：

1. 先尝试拿回原来的 `oldp`。
2. 原来的拿不到，再看看空闲 P 列表里有没有别的。

只要成功拿到一个 P，当前 G 就可以从 `_Gsyscall` 直接恢复成 `_Grunning`，继续往下执行。

这是最理想的路径。

### 6.8 慢速路径：拿不到 P，就别原地耗着

真正能体现调度器风格的，是慢速路径 `exitsyscall0`：

```go
func exitsyscall0(gp *g) {
	casgstatus(gp, _Gsyscall, _Grunnable)
	dropg()

	lock(&sched.lock)
	pp, _ := pidleget(0)
	if pp == nil {
		globrunqput(gp)
		locked := gp.lockedm != 0
		...
	} else if sched.sysmonwait.Load() {
		sched.sysmonwait.Store(false)
		notewakeup(&sched.sysmonnote)
	}
	unlock(&sched.lock)

	if pp != nil {
		acquirep(pp)
		execute(gp, false)
	}

	if locked {
		stoplockedm()
		execute(gp, false)
	}

	stopm()
	schedule()
}
```

这条路径的思路是：

1. 先把当前 G 从 `_Gsyscall` 改成 `_Grunnable`。
2. 解除 G 和 M 的绑定。
3. 再尝试拿一次空闲 P。
4. 如果拿到了，当前 M 继续执行这个 G。
5. 如果没拿到，就把 G 放回全局队列。
6. 当前 M 自己去休眠，等以后有 P 了再被唤醒。

这一步特别关键，因为它体现了 Go runtime 的取舍：

> 系统调用返回以后，如果当前 M 继续执行已经不划算，那就别硬撑，先把 G 交还给调度器，自己回空闲列表。

也就是说，**系统调用返回并不保证“一定由原来的 M 继续执行原来的 G”**。只要调度条件不合适，runtime 就会选择重新排队。

### 6.9 系统调用路径可以压缩成一句话

这一整套逻辑，如果只压缩成一句话，就是：

> 进入系统调用前，先把 G 现场存好、把 P 从 M 上拆下来；系统调用回来后，再尽量把 P 接回去，接不回去就把 G 还给调度器。

这也是为什么 Go 能在大量系统调用并发存在时，仍然尽量维持整体调度吞吐。

## 7. 休眠的 M 是怎么被唤醒的

前面几条路径都反复出现了一个动作：`wakep()`。

所以接下来要看的问题就很自然了：**休眠的 M 到底是怎么重新启动并回到调度循环的？**

### 7.1 哪些地方会触发 `wakep`

常见来源包括：

1. `newproc` 创建新 goroutine。
2. netpoll 发现 I/O 就绪，调用 `goready`。
3. `injectglist` 批量注入可运行 G。
4. `goschedImpl` 抢占后把 G 放回队列。
5. 特殊 goroutine 准备执行，比如 trace reader、GC worker。

最常见的还是 `newproc`：

```go
func newproc(fn *funcval) {
	...
	systemstack(func() {
		newg := newproc1(fn, gp, pc, false, waitReasonZero)
		pp := getg().m.p.ptr()
		runqput(pp, newg, true)

		if mainStarted {
			wakep()
		}
	})
}
```

注意这个条件：

```go
if mainStarted {
	wakep()
}
```

也就是说，只有 runtime 已经进入正常运行期以后，创建新的 goroutine 才会尝试拉起更多调度单元。

### 7.2 `wakep` 的策略很保守

看骨架：

```go
func wakep() {
	if sched.nmspinning.Load() != 0 || !sched.nmspinning.CompareAndSwap(0, 1) {
		return
	}

	mp := acquirem()

	var pp *p
	lock(&sched.lock)
	pp, _ = pidlegetSpinning(0)
	if pp == nil {
		if sched.nmspinning.Add(-1) < 0 {
			throw("wakep: negative nmspinning")
		}
		unlock(&sched.lock)
		releasem(mp)
		return
	}
	unlock(&sched.lock)

	startm(pp, true, false)
	releasem(mp)
}
```

这段代码体现了 runtime 的两个策略：

1. **如果已经有自旋 M 在找工作，就不要再多唤醒一个。**
2. **只有拿到空闲 P，才值得真正去拉起一个 M。**

换句话说，`wakep` 并不是“有新 G 就多开线程”，而是：

> 尽量少启动新的 MP 组合，只在调度器确实缺人干活时才补一个。

### 7.3 `startm` 才是真正的唤醒入口

`wakep` 只是做决策，真正完成“给一个 P 找个 M”的是 `startm`。

这段代码很长，但主线不复杂：

1. 先通过 `acquirem()` 禁止当前线程在关键时刻被抢占。
2. 尝试从空闲 M 列表拿一个已有的 M。
3. 拿不到时，必要时创建一个新的 M。
4. 把目标 P 放到这个 M 的 `nextp` 上。
5. 用 `notewakeup(&nmp.park)` 把它从休眠里叫醒。

核心思路如下：

```go
func startm(pp *p, spinning, lockheld bool) {
	mp := acquirem()
	...

	nmp := mget()
	if nmp == nil {
		id := mReserveID()
		unlock(&sched.lock)
		newm(fn, pp, id)
		releasem(mp)
		return
	}

	nmp.spinning = spinning
	nmp.nextp.set(pp)
	notewakeup(&nmp.park)
	releasem(mp)
}
```

这里有两个 runtime 工程细节值得记一下：

1. **能复用空闲 M，就尽量不创建新线程。**
2. **转移 P 所有权时，要先禁止当前线程被抢占，避免在 STW 等边界时刻把 P 搁在半空中。**

### 7.4 休眠的 M 醒来以后做什么

如果一个 M 是在 `stopm()` 里睡下去的，那么它醒来后通常会这样继续：

```go
func stopm() {
	gp := getg()
	...
	lock(&sched.lock)
	mput(gp.m)
	unlock(&sched.lock)

	mPark()
	acquirep(gp.m.nextp.ptr())
	gp.m.nextp = 0
}
```

也就是说，唤醒方已经提前把 P 填进了 `nextp`。M 醒来以后：

1. 先从 `nextp` 拿到 P。
2. 与 P 建立绑定。
3. 函数返回后重新进入 `schedule`。

如果是 `stoplockedm()`，逻辑类似，只是它不把 M 放回普通空闲列表，而是带着“锁定 G”的语义一起等待可用 P。

所以，M 的休眠和唤醒链路，可以压缩成一句话：

> 睡下去时把自己放进空闲 M 列表；唤醒时由别人先把 P 塞进 `nextp`，然后自己醒来接管这个 P，再回到调度循环。

## 8. GMP 并发度不是固定值，它会动态增减

很多人第一次接触 GMP 时，容易把它理解成一个固定的“线程池 + 队列”模型。但真正运行起来之后，你会发现它远比这个动态。

### 8.1 用户 `main.main` 跑起来之前，runtime 已经很忙了

在用户 `main.main` 真正开始执行之前，runtime 往往已经准备了若干后台角色，比如：

1. `sysmon`
2. `forcegchelper`
3. `bgsweep`
4. `bgscavenge`
5. finalizer 相关 goroutine

这些角色是否已经拥有独立的 M、何时进入休眠、何时再次被唤醒，都和平台、版本、时机有关。所以在调试器里看到几个后台 goroutine、几个线程，并不是一成不变的。

更稳妥的理解方式是：

> 用户代码开始之前，runtime 自己已经先把一部分后台调度、GC 和监控角色拉起来了。

### 8.2 新 goroutine 变多时，MP 组合为什么会增加

假设用户代码里短时间内创建出一批 goroutine，那么典型路径是：

1. `newproc` 把新 G 放进某个 P 的本地队列或 `runnext`。
2. `wakep` 尝试补一个自旋 M。
3. 新启动或新唤醒的 M 绑定某个空闲 P。
4. 它通过 `findRunnable` 或工作窃取拿到 G 开始执行。

所以从外部观察，会看到：

1. 活跃线程数上涨。
2. 更多 P 从空闲状态变成运行状态。
3. 本地队列里的 G 被逐步分散到多个 MP 组合上。

但这并不意味着“每创建一个 goroutine 就会多一个 M”。Go 调度器有很多抑制机制：

1. 已经有自旋 M 时，`wakep` 不会继续盲目扩张。
2. 空闲 P 数量有限。
3. 已经活跃的 M 可以通过 steal work 均衡负载。
4. 真正的并行上限仍然受 `GOMAXPROCS` 约束。

### 8.3 为什么后面又会降回去

当一波 goroutine 执行完，系统里剩余可运行 G 变少以后，找不到工作的 M 会逐步：

1. 先尝试本地队列、全局队列、netpoll、工作窃取。
2. 不行就释放 P。
3. 自己进入休眠，回到空闲 M 列表。

所以你看到的“并发度变化”，本质上不是 runtime 在做神秘魔法，而是：

1. 有活时补 MP。
2. 没活时回收 MP。

这也是 Go 能在轻载和高载之间自适应切换的关键。

### 8.4 一个容易误解的点：`main` 返回，程序就结束

这里再提醒一个常见误区。

如果 `main.main` 里只是启动了一批子 goroutine，但没有任何同步逻辑，那么主 goroutine 一旦返回，进程就会走退出路径。那些还没来得及执行、或者执行到一半的子 goroutine，也会一起结束。

所以调试时看到“goroutine 明明创建出来了，但怎么没跑完”，往往不是调度器没工作，而是：

> 主 goroutine 已经结束，进程整体退出了。

这一点和调度器是否还能继续找活，是两个层面的问题。

## 9. 总结

如果把本文压缩成几条最重要的结论，大概是下面这些：

1. goroutine 正常执行完成后，不是直接消失，而是回到 `goexit -> mcall -> goexit0 -> schedule` 这条收尾路径。
2. 长时间运行的 G，优先通过协作式抢占让出 M；只有在函数调用缺失时，runtime 才会进一步使用异步信号抢占。
3. 异步抢占的核心不是“直接中断调度”，而是通过信号处理修改 goroutine 的上下文，伪造一次对 `asyncPreempt` 的调用，再切回 `g0` 完成调度切换。
4. 系统调用前，runtime 会先把 G 改成 `_Gsyscall`，再把 P 从 M 上解绑；系统调用返回后，先尝试快速拿回 P，拿不到就把 G 交还给调度器。
5. `wakep -> startm -> notewakeup` 这条链路，负责把休眠的 M 再次拉回工作状态；而 `stopm/stoplockedm` 则负责在没有工作时把 M 安静地放回去。
6. GMP 的并发度不是固定的，它会随着可运行 G 的数量、空闲 P 的数量、自旋 M 的数量和系统调用阻塞情况动态变化。

如果把上一篇和这一篇合在一起看，可以得到一个更完整的认识：

1. 第一篇解决的是“Go 程序怎么启动起来”。
2. 这一篇解决的是“goroutine 在运行过程中是怎么被换下来的”。

再往后看，值得继续展开的主题其实还有很多，比如：

1. netpoll 和调度器的协作细节
2. channel、mutex 等等待队列是怎么挂进调度器的
3. GC safepoint、STW 与 goroutine 抢占之间的配合

但至少到这里，Go 调度器最核心的几条出入口已经基本连上了：

`执行 -> 抢占/阻塞/系统调用 -> 切回 g0 -> 修改状态 -> 回到 schedule -> 再执行`

理解这条循环，后面再看 runtime 的其他模块，会顺很多。
