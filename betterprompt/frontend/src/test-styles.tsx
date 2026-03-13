export function TestStyles() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-white mb-4">Tailwind CSS 测试页面</h1>
        <div className="bg-white rounded-2xl shadow-2xl p-6 mb-4">
          <h2 className="text-2xl font-semibold text-gray-800 mb-3">如果你能看到这些样式，说明 Tailwind 正常工作</h2>
          <p className="text-gray-600 mb-4">这个卡片有白色背景、圆角、阴影</p>
          <button className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-lg transition">
            测试按钮
          </button>
        </div>
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-red-500 text-white p-4 rounded-lg">红色</div>
          <div className="bg-green-500 text-white p-4 rounded-lg">绿色</div>
          <div className="bg-yellow-500 text-white p-4 rounded-lg">黄色</div>
        </div>
      </div>
    </div>
  );
}
