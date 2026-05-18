import Link from "next/link";

export default function Header() {
  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-screen-xl mx-auto px-4 py-3 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">CV</span>
          </div>
          <span className="font-bold text-xl text-gray-900">
            CVSkan<span className="text-indigo-600">.pl</span>
          </span>
        </Link>
        <div className="flex items-center gap-3">
          <button className="text-sm font-medium text-gray-500 hover:text-gray-900 transition-colors">
            Zaloguj się
          </button>
          <button className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors">
            Zacznij za darmo
          </button>
        </div>
      </div>
    </header>
  );
}
