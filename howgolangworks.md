# Go 程序是怎么跑起来的：从 `_rt0_arm64_linux` 到 `main.main`

> 基于 `Go 1.23` 和 `linux/arm64`，沿着程序入口、`runtime.rt0_go`、主 goroutine 创建和调度循环这条链路，把一个 Go 程序真正跑起来的过程走一遍。

## 1. 前言

在团队里聊 Go 并发时，`goroutine` 往往会被顺手说成“协程”。口头交流里这么说问题不大，但一旦开始追 runtime 源码，这种混用很容易把几个关键问题说糊：

1. `goroutine` 和一般意义上的 coroutine，到底是不是一回事？
2. `goroutine` 开得越多，系统就一定越快吗？
3. Go 号称可以支撑百万级 `goroutine`，这句话应该怎么理解？
4. Go 引以为傲的 GMP 调度模型，究竟是怎么把代码跑起来的？

Go 把并发写得很轻。业务开发里，识别出一段逻辑可以异步执行，前面加一个 `go`；需要同步，再补上 `sync` 或 `channel`。很多代码到这一步就已经能工作了。问题在于，“能工作”和“知道它为什么这样工作”之间，还隔着一整个 runtime。

本文不从概念定义入手，而是从一个最简单的 `hello world` 出发，顺着这条链路往下看：

`可执行文件 -> 程序入口 -> runtime.rt0_go -> main goroutine -> schedule -> runtime.main -> main.main`

如果把这条链路看明白，Go 程序是怎么启动、怎么创建主 goroutine、怎么切栈、怎么进入调度循环，基本也就有了整体轮廓。

## 2. 阅读前提

这篇文章默认读者已经有以下基础：

1. 了解进程、线程、协程的基本区别。
2. 了解函数调用、栈帧、寄存器这些概念。
3. 了解操作系统调度的基本思路，知道协作式和抢占式的区别。
4. 了解 Go 并发编程的常见工具：`goroutine`、`mutex`、`atomic`、`channel`、`signal`。
5. 了解一些 Linux 基础，尤其是系统调用和 I/O 多路复用。
6. 对 Go 内存管理有粗略印象，知道 `mcache`、`mcentral`、`mheap` 这些名字。

如果你是第一次读 runtime，不必一口气把所有细节都吃透。本文真正的主线只有一条：**Go 程序启动后，是如何把第一个用户级执行流跑起来的。**

## 3. 一个最简单的 Go 程序（Hello World）

```go
package main

import "fmt"

func main() {
	fmt.Println("hello world")
}
```

这个程序几乎每个 Go 开发者都写过。本文不关心它输出了什么，只关心一件事：`hello world` 是怎么被打印出来的？

先给出本文主线：

`_rt0_arm64_linux -> main -> runtime.rt0_go -> schedinit -> newproc(runtime.main) -> mstart -> schedule -> runtime.main -> main.main`

后文就是把这条链路一点一点拆开。

### 3.1 基础知识

#### 3.1.1 操作系统

操作系统负责管理硬件和软件资源，对上提供进程、线程、文件、网络、内存等抽象。我们平时写的 Go 程序，本质上仍然跑在操作系统的进程和线程模型之上。

#### 3.1.2 处理器架构与指令集

本文默认分析环境是 `linux/arm64`。处理器架构决定了寄存器布局、指令格式、调用约定等底层细节，因此同样的 Go runtime，在不同平台上的汇编入口并不相同。

常见组合大致如下：

| 系统 | 常见架构 |
| --- | --- |
| Linux | `x86_64`、`arm64`、`riscv64` |
| macOS | `x86_64`、`arm64` |
| Windows | `x86_64`、`arm64` |

#### 3.1.3 编译工具链与可执行文件

高级语言代码最终都会变成可执行文件。以 C 为例，通常会经过：

1. 预处理
2. 编译
3. 汇编
4. 链接

不同操作系统的可执行文件格式不同：

| 操作系统 | 文件格式 | 说明 |
| --- | --- | --- |
| Windows | PE | Windows 平台的可执行/动态链接格式 |
| Linux | ELF | Unix/Linux 常见格式 |
| macOS | Mach-O | macOS 使用的目标文件格式 |

Go 编译器当然不会完全照搬 C 的编译流程，但“最终得到一个带入口地址的可执行文件”这件事是一样的。也正因为如此，我们才有可能从二进制层面反推程序到底是从哪里开始执行的。

### 3.2 程序真正从哪里开始

结论先行：**`main.main` 不是 Go 程序的入口点。**

下文默认以 `Go 1.23`、`linux/arm64` 为分析环境。不同 Go 版本在函数行号、局部实现和少量调度细节上可能会有出入，但本文这条主线不会变。

对 Go 开发者来说，`main` 包里的 `main()` 看起来很像“程序起点”；但对操作系统来说，它只认可执行文件里的入口地址。想确认这一点，先把示例程序编成一个二进制：

```bash
go build -o main main.go
```

然后用 `readelf` 看 ELF 头：

```bash
$ readelf --file-header main
ELF Header:
  Magic:   7f 45 4c 46 02 01 01 00 00 00 00 00 00 00 00 00
  Class:                             ELF64
  ...
  Entry point address:               0x746c0
  ...
```

这里给出的 `Entry point address`，才是操作系统加载完程序后真正跳转的第一条指令地址。这个地址显然不是 `main.main`。

继续用 `nm` 查一下对应符号：

```bash
$ nm -n main | grep 746c0
00000000000746c0 T _rt0_arm64_linux
```

可以看到，`linux/arm64` 下真正的入口符号是 `_rt0_arm64_linux`。

对应源码在 `src/runtime/rt0_linux_arm64.s`：

```asm
TEXT _rt0_arm64_linux(SB),NOSPLIT|NOFRAME,$0
	MOVD	0(RSP), R0
	ADD	$8, RSP, R1
	BL	main(SB)
```

这段代码本身很短，只做了两件事：

1. 从当前栈上取出 `argc` 和 `argv`。
2. 跳到同文件里的 `main` 标签继续执行。

继续往下看：

```asm
TEXT main(SB),NOSPLIT|NOFRAME,$0
	MOVD	$runtime·rt0_go(SB), R2
	BL	(R2)
```

这里的含义很直接：把 `runtime.rt0_go` 的地址装进寄存器，然后跳过去执行。

这一节先记一句话：

> `linux/arm64` 下，Go 程序先从 `_rt0_arm64_linux` 进入，再转到 `runtime.rt0_go`，后者才是 Go runtime 真正的启动入口。

<details>
<summary>补充：为什么这里还会看到 fallback 退出逻辑？</summary>

正常情况下，Go 程序会在 `main.main` 返回后，由 runtime 走完整的退出流程。但如果 `runtime.rt0_go` 在初始化期就发生严重错误，程序甚至来不及建立完整的 runtime 状态，这时就只能走更底层的兜底退出路径，直接发起系统调用终止进程。

所以，入口附近出现一小段 fallback 逻辑并不奇怪，它不是常规路径，而是“初始化都没起来”时的保险丝。

</details>

### 3.3 `runtime.rt0_go` 到底做了什么

`runtime.rt0_go` 是 Go 程序从“刚被操作系统拉起来”进入“已经具备 Go 运行环境”的关键分界线。

如果把启动过程压缩成一句话，那就是：

**先把 runtime 自己站稳，再创建第一个 goroutine，然后把控制权交给调度器。**

在继续往下追之前，先把几个基本角色说清楚。

#### 3.3.1 先把角色说清楚：G、M、P、g0

GMP 这三个字母经常一起出现，但初学时最容易混淆的恰恰是“它们各自管什么”。

| 名称 | 含义 | 关键职责 |
| --- | --- | --- |
| G | goroutine | 用户任务和执行上下文，带独立栈 |
| M | machine | runtime 对系统线程的抽象，负责真正执行代码 |
| P | processor | 调度上下文和本地资源拥有者 |
| g0 | 系统 goroutine | 每个 M 都有一个，专门跑 runtime 代码 |

先记住三句话：

1. **G 是被调度对象。**
2. **M 是实际执行者。**
3. **P 不是 CPU 核，也不是线程，它更像 runtime 给 M 发的“执行资格”和“本地资源包”。**

为什么说 P 是“本地资源包”？因为凡是想避免全局锁竞争的东西，runtime 都倾向于先挂在 P 上。比如本地运行队列、`mcache`、`gFree`、部分 timer 结构等，都和 P 紧密相关。

再说一句经常被混用的话题：`goroutine` 和 coroutine 到底是不是一回事？

日常交流里，把 `goroutine` 说成“协程”不是完全不行；但如果是在严肃技术写作里，最好还是直接写 `goroutine`。原因主要有两个：

1. `goroutine` 不是一个纯语言层的 coroutine 抽象，它和 Go runtime 的栈管理、GC、netpoll、sysmon、抢占逻辑都深度绑定。
2. 从 Go 1.14 开始，`goroutine` 不只是“主动让出”这么简单，它还支持基于信号的异步抢占。

也就是说，Go 的调度模型不能简单概括成一句“协程调度”。写文章时，术语分开会更准确。

#### 3.3.2 第一步：先把 `g0` 搭起来

`runtime.rt0_go` 进入后的第一件关键工作，是把 `g0` 初始化出来。

这一点非常重要，因为 Go runtime 里有很多事情**不能**在普通 goroutine 的用户栈上做：

1. 普通 goroutine 的栈初始很小，而且会动态扩缩容，不够稳定。
2. 调度、栈扩容、信号处理、系统调用切换这类逻辑，需要一个更可控的执行环境。
3. goroutine 退出时要回收自己的栈，显然不能站在自己的栈上做清理。

这就是 `g0` 存在的意义：**每个 M 都会绑定一个专用的系统 goroutine，运行时的重要工作都尽量在它的栈上完成。**

`rt0_go` 里相关汇编大致如下：

```asm
MOVD	$runtime·g0(SB), g
MOVD	RSP, R7
MOVD	$(-64*1024)(R7), R0
MOVD	R0, g_stackguard0(g)
MOVD	R0, g_stackguard1(g)
MOVD	R0, (g_stack+stack_lo)(g)
MOVD	R7, (g_stack+stack_hi)(g)
```

这段代码做的事情并不复杂：它拿当前线程已有的栈空间，先切出一段给 `g0` 使用，然后把 `stack.lo`、`stack.hi`、`stackguard` 这些关键字段填好。

这里有两个结论值得单独记一下：

1. `g0` 是每个 M 自带的，不是全局只有一个。
2. 后面凡是涉及调度、切栈、系统调用切换、goroutine 回收，你大概率都会看到代码先切回 `g0`。

<details>
<summary>补充：为什么说用户栈“不稳定”？</summary>

普通 goroutine 的栈会按需增长和收缩。只要栈发生扩容，旧栈内容就可能被整体搬迁到一块新内存上，栈上对象的地址也会随之变化。

这就是为什么 runtime 不愿意在用户栈上长期保存那些对“地址稳定性”要求很高的调度状态。顺着这个角度去理解，也更容易明白两件常被问到的事：

1. 为什么 Go 不允许直接取 `map` 元素地址。
2. 为什么把指针随手转成 `uintptr` 再跨越函数边界保存，会有风险。

它们背后都和“对象地址不一定稳定”有关。

</details>

#### 3.3.3 第二步：让 `m0` 和 `g0` 建立绑定

`g0` 搭好之后，接下来要做的是把它和启动线程绑定起来。

启动程序的第一个线程，在 Go runtime 里叫 `m0`。对应汇编很短：

```asm
MOVD	$runtime·m0(SB), R0
MOVD	g, m_g0(R0)
MOVD	R0, g_m(g)
```

短短三行，做的是双向绑定：

1. `m0.g0 = g0`
2. `g0.m = m0`

从这一刻开始，Go runtime 至少已经拥有了第一个可用的执行单元：

- 一个真实的系统线程：`m0`
- 一个稳定的系统栈：`g0`

后面所有初始化动作，都会以这对组合为基础继续往下走。

#### 3.3.4 第三步：初始化 runtime 的核心组件

`g0` 和 `m0` 准备好之后，`rt0_go` 接下来会调用几个真正重量级的初始化函数：

```asm
BL	runtime·args(SB)
BL	runtime·osinit(SB)
BL	runtime·schedinit(SB)
```

这三个函数里，最关键的是 `schedinit`。

先分别看一下它们做什么：

1. `runtime.args`：整理命令行参数。
2. `runtime.osinit`：读取平台相关信息，比如 CPU 数量、huge page 信息。
3. `runtime.schedinit`：初始化调度器、内存分配器、GC、P 池、各种全局状态。

##### `runtime.args`

这一层主要是把入口处拿到的 `argc`、`argv` 调整成 Go runtime 能继续使用的布局，后面 `os.Args` 才有机会工作起来。

##### `runtime.osinit`

以 Linux 为例，`osinit` 会做几件平台相关的工作：

1. 通过 `sched_getaffinity` 之类的机制拿到当前进程可用 CPU 数。
2. 读取系统 huge page 信息。
3. 做架构相关的补充初始化。

这些信息后面都会影响调度器和内存管理器的行为。

##### `runtime.schedinit`

重头戏是 `schedinit`。它的职责可以概括成一句话：

**把一个“刚被拉起来的线程”，变成一个具备 Go 调度能力的运行时环境。**

源码很长，先只抓主线：

```go
func schedinit() {
	lockInit(&sched.lock, lockRankSched)
	...

	gp := getg()
	sched.maxmcount = 10000

	worldStopped()

	stackinit()
	mallocinit()
	...
	mcommoninit(gp.m, -1)
	gcinit()

	lock(&sched.lock)
	procs := ncpu
	if n, ok := atoi32(gogetenv("GOMAXPROCS")); ok && n > 0 {
		procs = n
	}
	if procresize(procs) != nil {
		throw("unknown runnable goroutine during bootstrap")
	}
	worldStarted()
}
```

这段代码里值得重点看的有四件事：

1. 初始化锁、栈、分配器、GC 等基础模块。
2. 把 `m0` 加入全局 M 链表。
3. 根据 `GOMAXPROCS` 决定要创建多少个 P。
4. 通过 `procresize` 真正把 P 池建起来。

`procresize` 是理解启动阶段的关键，它负责初始化 `allp`，并把第一个 P 绑定给当前线程：

```go
func procresize(nprocs int32) *p {
	...
	for i := old; i < nprocs; i++ {
		pp := allp[i]
		if pp == nil {
			pp = new(p)
		}
		pp.init(i)
		atomicstorep(unsafe.Pointer(&allp[i]), unsafe.Pointer(pp))
	}

	gp := getg()
	pp := allp[0]
	pp.status = _Pidle
	acquirep(pp)
	...
}
```

这里可以直接记结论：

1. `procresize` 会把 `allp[0]` 绑定给当前 M，也就是 `m0`。
2. 启动结束后，`m0 <-> p0` 这对组合已经建立起来了。
3. 其他 P 先进入空闲列表，等后面需要时再被其他 M 拿走。

也就是说，执行到这里，runtime 至少已经有了这几样东西：

1. `m0`
2. `g0`
3. `p0`
4. 一组空闲的 P
5. 已经可用的内存分配器和 GC 基础设施

这一段可以收束成一句话：

> `schedinit` 做的不是“调几项配置”，而是在真正意义上把 Go 运行时搭起来。

##### P 上到底挂了什么资源

很多资料喜欢把 P 介绍成“逻辑处理器”，这没错，但还不够具体。P 更重要的身份其实是：**本地资源的拥有者。**

一个 P 上比较关键的本地状态包括：

1. 本地运行队列 `runq` 和高优先级槽位 `runnext`
2. `mcache`
3. `gFree`
4. timer 相关结构
5. 若干与栈缓存、`sudog`、`defer` 相关的本地缓存

理解这一点后，很多设计就会顺理成章：为什么 M 必须先拿到 P 才能跑 Go 代码？因为没有 P，就拿不到这些本地资源。

#### 3.3.5 第四步：创建第一个 goroutine

到这里，runtime 自己已经站稳了。接下来才轮到第一个要跑的 goroutine 出场。

这里很容易有一个误解：**启动阶段创建出来的第一个 goroutine，承载的是 `runtime.main`，不是用户写的 `main.main`。**

对应汇编在 `rt0_go` 里大致是这样：

```asm
MOVD	$runtime·mainPC(SB), R0
SUB	$16, RSP
MOVD	R0, 8(RSP)
MOVD	$0, 0(RSP)
BL	runtime·newproc(SB)
ADD	$16, RSP

DATA	runtime·mainPC+0(SB)/8,$runtime·main<ABIInternal>(SB)
GLOBL	runtime·mainPC(SB),RODATA,$8
```

这段代码的含义很直接：

1. 准备好 `runtime.main` 的函数地址。
2. 调用 `runtime.newproc`。
3. 创建一个新的 goroutine，目标函数就是 `runtime.main`。

也就是说，Go 程序不是“直接跳进 `main.main`”，而是**先把 `runtime.main` 包装成第一个待运行 goroutine**。

##### `newproc` 做了什么

`newproc` 可以理解成 Go 层创建 goroutine 的统一入口。你平时写的：

```go
go f()
```

编译器最终也会落到这里。

核心逻辑大致如下：

```go
func newproc(fn *funcval) {
	pc := getcallerpc()
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

这段代码里有两个关键点：

1. 负责分配并构造 goroutine 实体的是 `newproc1`。
2. 这些工作会先切到 `g0` 上执行，也就是通过 `systemstack` 完成。

为什么要先上 `g0`？原因前面已经埋过伏笔了：创建 goroutine 需要改调度状态、分配栈、构造调度上下文，这些都更适合在系统栈上做。

<details>
<summary>`systemstack` 的核心思路</summary>

`systemstack` 的本质并不神秘，它做的事情可以概括成四步：

1. 判断当前是不是已经在系统栈上。
2. 如果不是，就把当前 goroutine 的现场保存到它自己的 `gobuf`。
3. 把 `g` 寄存器和栈指针切换到 `g0`。
4. 在 `g0` 栈上执行传入函数，结束后再切回原来的 goroutine。

这也是后面理解调度、抢占、系统调用切换的一个重要前置知识：**Go 的很多运行时动作，本质上都是“先保存当前 G，再切到 g0 干活”。**

</details>

##### `newproc1`：真正创建 goroutine 实体

`newproc1` 是整个创建流程里最核心的一段：

```go
func newproc1(fn *funcval, callergp *g, callerpc uintptr, parked bool, waitreason waitReason) *g {
	mp := acquirem()
	pp := mp.p.ptr()

	newg := gfget(pp)
	if newg == nil {
		newg = malg(stackMin)
	}

	totalSize := uintptr(4*goarch.PtrSize + sys.MinFrameSize)
	totalSize = alignUp(totalSize, sys.StackAlign)
	sp := newg.stack.hi - totalSize

	newg.sched.sp = sp
	newg.stktopsp = sp
	newg.sched.pc = abi.FuncPCABI0(goexit) + sys.PCQuantum
	newg.sched.g = guintptr(unsafe.Pointer(newg))
	gostartcallfn(&newg.sched, fn)

	newg.startpc = fn.fn
	gcController.addScannableStack(pp, int64(newg.stack.hi-newg.stack.lo))
	casgstatus(newg, _Gdead, _Grunnable)
	newg.goid = pp.goidcache
	pp.goidcache++
	releasem(mp)
	return newg
}
```

拆开看只有四步：

1. 先尝试从 `gFree` 复用一个旧的 G；拿不到就新建。
2. 为它准备一块初始栈。
3. 初始化 `sched`，也就是这个 goroutine 未来恢复执行所需的现场。
4. 把状态从 `_Gdead` 改成 `_Grunnable`。

最容易看晕的地方在这里：

```go
newg.sched.pc = abi.FuncPCABI0(goexit) + sys.PCQuantum
gostartcallfn(&newg.sched, fn)
```

看起来像是先把 `pc` 设成了 `goexit`，随后又调用 `gostartcallfn`。这不是多此一举，而是在**伪造一个合法的调用现场**。

##### 为什么要把 `goexit` 预先塞进去

一个新 goroutine 第一次被调度时，它并不是从“某个正常调用点”恢复出来的，而是 runtime 凭空构造出来的。

问题在于：目标函数执行完以后，总得有一个统一的“收尾入口”。

Go 的做法是：

1. 先把 `goexit` 的地址放进调度上下文里。
2. 再通过 `gostartcallfn` 把真正要执行的函数地址写到 `pc`，把“返回地址”挪到 `lr`。

这样一来，第一次调度时这个 G 会从目标函数开始跑；目标函数返回后，又会自然落回 `goexit`，由 runtime 接管后续清理。

`gostartcallfn` 的逻辑可以简单理解成：

```go
func gostartcallfn(gobuf *gobuf, fv *funcval) {
	var fn unsafe.Pointer
	if fv != nil {
		fn = unsafe.Pointer(fv.fn)
	} else {
		fn = unsafe.Pointer(abi.FuncPCABIInternal(nilfunc))
	}
	gostartcall(gobuf, fn, unsafe.Pointer(fv))
}

func gostartcall(buf *gobuf, fn, ctxt unsafe.Pointer) {
	buf.lr = buf.pc
	buf.pc = uintptr(fn)
	buf.ctxt = ctxt
}
```

这里可以记一句更关键的话：

> goroutine 不是“只有函数指针”就能跑起来，它必须先被 runtime 构造成一个完整的可恢复执行现场。

##### 主 goroutine 会先放到哪里

`newproc` 创建出主 goroutine 后，接着会调用：

```go
runqput(pp, newg, true)
```

这里的 `pp` 就是当前 `g0` 所在 M 绑定的 P，也就是启动阶段的 `p0`。而且 `true` 这个参数意味着它优先走 `runnext`，所以第一个 goroutine 几乎一定会被优先调度。

<details>
<summary>为什么一定是 `p0`？</summary>

因为在 `schedinit -> procresize` 里，`m0` 已经通过 `acquirep(allp[0])` 和 `p0` 建立了绑定关系。

而 `newproc` 是在 `g0` 上执行的，此时：

1. `getg()` 返回的是 `g0`
2. `getg().m` 是 `m0`
3. `m0.p` 指向的正是 `p0`

所以主 goroutine 的第一次入队，天然就落在 `p0` 上。

</details>

#### 3.3.6 第五步：启动调度循环

主 goroutine 创建出来以后，`rt0_go` 接下来会调用：

```asm
BL	runtime·mstart(SB)
```

从这里开始，程序就从“启动阶段”进入“调度阶段”了。

`mstart` 很短，关键在它后面的 Go 代码：

```go
func mstart0() {
	gp := getg()
	...
	gp.stackguard0 = gp.stack.lo + stackGuard
	gp.stackguard1 = gp.stackguard0
	mstart1()
	mexit(osStack)
}

func mstart1() {
	gp := getg()
	gp.sched.g = guintptr(unsafe.Pointer(gp))
	gp.sched.pc = getcallerpc()
	gp.sched.sp = getcallersp()

	asminit()
	minit()

	if gp.m == &m0 {
		mstartm0()
	}

	if gp.m != &m0 {
		acquirep(gp.m.nextp.ptr())
		gp.m.nextp = 0
	}

	schedule()
}
```

对本文主线，只需要记住两点：

1. `mstart0/mstart1` 会把当前 M 对应的 `g0` 栈规则补齐。
2. 最终会进入 `schedule()`，而且正常情况下不会返回。

至于 `asminit`、`minit`、`mstartm0` 这些细节，知道它们分别对应“平台初始化”“线程本地初始化”“m0 的一次性特殊任务”就够用了。沿着 `hello world` 这条主线，真正必须看懂的是 `schedule`。

##### `schedule` 的核心逻辑

把异常分支和边角处理先去掉，`schedule` 的主干可以压缩成这样：

```go
func schedule() {
	mp := getg().m

top:
	pp := mp.p.ptr()
	pp.preempt = false

	gp, inheritTime, tryWakeP := findRunnable()

	if mp.spinning {
		resetspinning()
	}
	if tryWakeP {
		wakep()
	}
	if gp.lockedm != 0 {
		startlockedm(gp)
		goto top
	}

	execute(gp, inheritTime)
}
```

它本质上只干一件事：

**找一个可运行的 G，然后把它交给当前 M 去执行。**

难点不在 `schedule` 本身，而在 `findRunnable`。

##### `findRunnable` 在按什么顺序找工作

`findRunnable` 很长，但它的查找顺序是有层次的。精简后可以概括成下面这份优先级表：

1. 特殊 goroutine，比如 trace reader、GC worker。
2. 周期性地看一眼全局队列，避免本地队列长期独占执行机会。
3. 当前 P 的本地运行队列 `runq/runnext`。
4. 全局运行队列。
5. `netpoll` 返回的可运行 G。
6. 工作窃取，从其他 P 的本地队列里偷一部分任务。
7. 如果当前正处于 GC 标记期，而且有空闲标记工作，就转去跑 GC worker。
8. 如果真的什么都没有，再决定是自旋还是休眠。

所以，如果把启动场景代进去，就很好理解了：

- `p0` 的 `runnext` 上已经有刚才创建的主 goroutine
- `findRunnable` 很快就会把它取出来
- 然后交给 `execute`

这就是第一个用户级执行流真正要开始跑的时刻。

##### 自旋、休眠和工作窃取

这部分是 Go 调度器最经典也最容易讲散的话题。本文只抓必要结论。

当一个 M 本地没活可干时，它不会立刻睡下去，而是会先尝试做两件事：

1. 看看全局队列和 `netpoll` 有没有现成工作。
2. 尝试从其他 P 窃取一部分任务。

为了避免所有空闲线程都疯狂空转，Go 又引入了“自旋 M 数量受限”的机制。简单理解就是：**允许少量 M 保持活跃寻找工作，但不会让它们无限制地烧 CPU。**

找不到工作时，M 会释放当前 P，让 P 先回空闲列表，自己再进入休眠。等后面有新工作进来，runtime 会再把某个空闲 M 唤醒，并给它重新分配 P。

<details>
<summary>补充：工作窃取的遍历顺序为什么不是固定的？</summary>

如果所有空闲 P 都总是按固定顺序去偷，比如永远先看 `p0`、再看 `p1`，那某几个热点 P 就会被持续骚扰，负载均衡效果反而会变差。

Go 的做法是为窃取过程生成一个近似随机、但又无需高成本随机数的遍历序列。源码里相关结构叫 `randomOrder`，核心思路是预先计算若干与 `count` 互质的步长，用“起点 + 步长取模”的方式，低成本地遍历全部 P。

这部分实现很巧，但和本文主线关系不算强，知道它解决的是“窃取顺序随机化”就够了。

</details>

#### 3.3.7 真正切到主 goroutine：`execute` 与 `gogo`

`schedule` 找到主 goroutine 后，会进入 `execute`：

```go
func execute(gp *g, inheritTime bool) {
	mp := getg().m
	mp.curg = gp
	gp.m = mp
	casgstatus(gp, _Grunnable, _Grunning)
	gogo(&gp.sched)
}
```

这里有三件事：

1. `mp.curg = gp` 和 `gp.m = mp` 建立了当前 M 与当前运行 G 的双向绑定。
2. `casgstatus` 把 G 的状态从 `_Grunnable` 原子地改成 `_Grunning`。
3. `gogo(&gp.sched)` 负责真正完成上下文切换。

`gogo` 是 runtime 里最经典的一段“恢复现场”逻辑。它接收一个 `gobuf`，把里面保存好的寄存器值重新装回 CPU，然后直接跳到目标 PC 去执行。

相关结构大致长这样：

```go
type gobuf struct {
	sp   uintptr
	pc   uintptr
	g    guintptr
	ctxt unsafe.Pointer
	ret  uintptr
	lr   uintptr
	bp   uintptr
}
```

核心汇编逻辑可以概括成：

```asm
MOVD gobuf_g(R5), R6
MOVD R6, g
BL runtime.save_g(SB)

MOVD gobuf_sp(R5), R0
MOVD R0, RSP
MOVD gobuf_bp(R5), R29
MOVD gobuf_lr(R5), LR
MOVD gobuf_ctxt(R5), R26
MOVD gobuf_pc(R5), R6
B (R6)
```

也就是说，`gogo` 做的不是“调用一个函数”，而是：

1. 把当前线程视角下的“当前 goroutine”切成目标 G。
2. 把栈指针从 `g0` 的系统栈切到目标 goroutine 的用户栈。
3. 恢复目标 G 的调用现场。
4. 直接跳到它的下一条待执行指令。

执行到这里，`m0` 已经不再运行在 `g0` 栈上了，而是切到了主 goroutine 的栈上。此时真正开始执行的，就是刚才创建出来的那个 goroutine 对应的目标函数：`runtime.main`。

#### 3.3.8 `runtime.main` 如何走到用户的 `main.main`

前面提到过，主 goroutine 承载的不是用户 `main.main`，而是 `runtime.main`。所以接下来真正要看的，是 `runtime.main` 自己做了什么。

主干逻辑大致如下：

```go
func main() {
	mp := getg().m

	if goarch.PtrSize == 8 {
		maxstacksize = 1000000000
	} else {
		maxstacksize = 25000000
	}

	mainStarted = true

	if haveSysmon {
		systemstack(func() {
			newm(sysmon, nil, -1)
		})
	}

	lockOSThread()
	if mp != &m0 {
		throw("runtime.main not on m0")
	}

	doInit(runtime_inittasks)

	needUnlock := true
	defer func() {
		if needUnlock {
			unlockOSThread()
		}
	}()

	gcenable()

	for m := &firstmoduledata; m != nil; m = m.next {
		doInit(m.inittasks)
	}

	needUnlock = false
	unlockOSThread()

	fn := main_main
	fn()
	...
}
```

这段代码里和主线最相关的事情有五件：

1. 把 `mainStarted` 置为 `true`，允许后续 `newproc` 真的去唤醒更多执行单元。
2. 启动 `sysmon` 线程。
3. 执行 runtime 自己的初始化任务。
4. 开启 GC，并按依赖顺序执行各个包的 `init`。
5. 最后通过 `main_main` 间接调用用户写的 `main.main`。

走到这里，用户代码才真正登场。

`hello world` 的输出，正是在这一步发生的：

```go
func main() {
	fmt.Println("hello world")
}
```

从“程序启动”这个角度回看，`fmt.Println("hello world")` 前面其实已经发生了很多事情：

1. 二进制被操作系统加载。
2. `_rt0_arm64_linux` 把控制权交给 `runtime.rt0_go`。
3. runtime 初始化了 `g0`、`m0`、`p0`、P 池、内存分配器和 GC。
4. runtime 创建了主 goroutine。
5. 调度器把主 goroutine 调度起来。
6. `runtime.main` 跑完了自己的准备工作。
7. 用户 `main.main` 才开始执行。

这也是为什么说：**Go 程序看起来是从 `main.main` 开始，实际上远远不是。**

这也解释了一个很常见的现象：如果你在 `main` 里只起了一个 goroutine，然后自己很快返回，程序会直接退出，那个新起的 goroutine 甚至可能还没来得及跑。

原因很简单：`main goroutine` 结束，进程就准备退出了。想等其他 goroutine 跑完，得靠 `WaitGroup`、阻塞 `channel` 或其他同步手段把主流程拦住。

#### 3.3.9 goroutine 执行完以后，runtime 怎么收尾

前面在 `newproc1` 里埋过一颗钉子：新 goroutine 的返回地址被预先设置成了 `goexit`。

所以当 goroutine 绑定的目标函数执行完，最终不会“凭空消失”，而是会自然落到 `goexit`：

```asm
TEXT runtime.goexit(SB), NOSPLIT|NOFRAME|TOPFRAME,$0-0
	MOVD R0, R0
	BL runtime.goexit1(SB)
```

后面继续进入：

```go
func goexit1() {
	...
	mcall(goexit0)
}
```

这里最关键的是 `mcall(goexit0)`。它的含义是：**把当前 goroutine 的现场保存好，然后切回当前 M 的 `g0` 栈，在系统栈上执行 `goexit0`。**

为什么又要回 `g0`？

因为 goroutine 退出时要做的事，包括：

1. 回收栈
2. 清理状态
3. 放回 `gFree`
4. 重新进入调度

这些事情都不适合在它自己的用户栈上做。道理很朴素：你不能站在一把椅子上把它拆掉。

`mcall` 的核心动作就是：

1. 保存当前 G 的 `sp`、`bp`、`pc`
2. 切换 `g` 到 `m.g0`
3. 切换栈指针到 `g0` 的系统栈
4. 调用目标函数 `goexit0`

而 `goexit0` 的逻辑非常直接：

```go
func goexit0(gp *g) {
	gdestroy(gp)
	schedule()
}
```

这就把整条链闭环了：

1. 当前 G 执行完
2. 切回 `g0`
3. 回收当前 G
4. 再次进入 `schedule`
5. 找下一个可运行 G

这就是 Go 调度循环真正“转起来”的方式。

需要单独说明的一点是：**主 goroutine 的退出和普通 goroutine 不完全一样。**

普通 goroutine 通常会走 `goexit -> goexit0 -> schedule` 这条路；而主 goroutine 执行完以后，runtime 走的是进程退出逻辑。也正因为如此，`main.main` 一旦返回，其他 goroutine 通常也就一起结束了。

## 总结

从 `hello world` 这个最小示例往下追，Go 程序的启动路径可以收束成下面这条主线：

1. 操作系统从 ELF 入口 `_rt0_arm64_linux` 开始执行。
2. 入口汇编把控制权交给 `runtime.rt0_go`。
3. `rt0_go` 初始化 `g0`、`m0`，再通过 `schedinit` 把调度器、GC、内存分配器和 P 池搭起来。
4. runtime 创建承载 `runtime.main` 的主 goroutine，并把它放进 `p0` 的可运行队列。
5. `mstart -> schedule -> findRunnable -> execute -> gogo` 这一套逻辑把主 goroutine 真正调度起来。
6. `runtime.main` 做完 runtime 级初始化后，才调用到用户写的 `main.main`。
7. goroutine 执行结束后，再由 `goexit/mcall/goexit0` 回到 `g0` 做统一回收。

回到文章开头那几个问题，现在可以给出更清晰的答案了：

1. 写技术文章时，`goroutine` 最好不要直接等同于“协程”。
2. `goroutine` 数量增加，不会自动等于性能提升；真正的瓶颈仍然取决于 CPU、I/O、锁竞争、内存占用和调度开销。
3. “百万 goroutine”说的是运行时模型具备这种能力，不代表业务场景里应该盲目追求这个数字。
4. Go 所谓的 GMP，本质上是让大量 G 复用少量 M，并借助 P 持有本地资源，再由 `g0` 承担运行时敏感逻辑。

如果把本文压缩成一句话，那就是：

> Go 程序不是“从 `main.main` 直接开始跑”，而是 runtime 先把自己的世界搭起来，再把用户代码接进去。

理解这一点，后面再去看 goroutine 抢占、系统调用切换、网络轮询、GC 与调度协作，都会顺畅很多。
