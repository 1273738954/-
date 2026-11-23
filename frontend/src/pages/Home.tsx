import { useNavigate } from "react-router-dom"
import PageHeader, { HeaderIconButton } from "@/components/PageHeader"
import TodayMealCard from "@/components/TodayMealCard"
import { cardShadow } from "@/components/Card"
import { useAuthStore } from "@/store/useAuthStore"
import { useAppInfoStore } from "@/store/useAppInfoStore"
import { Home as HomeIcon, Settings } from "lucide-react"

function getGreeting(): string {
  const h = new Date().getHours()
  if (h < 6) return "夜深了~"
  if (h < 11) return "早上好 ☀️"
  if (h < 14) return "中午好 🍳"
  if (h < 18) return "下午好 ☀️"
  return "晚上好 🌙"
}

export default function Home() {
  const navigate = useNavigate()
  const isLoggedIn = useAuthStore((s) => s.isLoggedIn)
  const appName = useAppInfoStore((s) => s.appName)

  return (
    <div className="animate-fadeUp">
      <PageHeader
        title={<span>{appName.slice(0, Math.max(1, appName.length - 4))}<span className="text-primary">{appName.slice(Math.max(1, appName.length - 4))}</span></span>}
        subtitle="今天也好好吃饭"
        icon={HomeIcon}
        actions={
          <HeaderIconButton onClick={() => navigate(isLoggedIn ? "/admin/dashboard" : "/admin/login")} aria-label="管理设置">
            <Settings size={18} strokeWidth={2.3} />
          </HeaderIconButton>
        }
      />

      <div className="px-5 py-4 max-w-[640px] mx-auto">
        <div className="mb-5">
          <div className="text-sm text-text2 mb-1">{getGreeting()}</div>
          <div className="text-[26px] font-extrabold tracking-tight leading-tight">今天<em className="not-italic text-primary">吃了什么</em>？</div>
        </div>

        {/* 今日记录：沿用记录页的卡片样式与交互 */}
        <TodayMealCard />

        {/* 明天吃什么 */}
        <button
          onClick={() => navigate("/tomorrow")}
          className={`w-full bg-card rounded-2xl p-4 ${cardShadow} border border-border flex items-center gap-3.5 transition-all active:scale-98`}
        >
          <div className="w-12 h-12 rounded-[10px] bg-gradient-to-br from-yellow-light to-primary-light flex items-center justify-center text-2xl flex-shrink-0">🌙</div>
          <div className="flex-1 min-w-0 text-left">
            <div className="text-[15px] font-bold mb-0.5">🌙 明天吃什么？</div>
            <div className="text-xs text-text2">提前规划明天的菜单，不用再临时纠结</div>
          </div>
          <span className="text-text3 text-sm">›</span>
        </button>
      </div>
    </div>
  )
}
