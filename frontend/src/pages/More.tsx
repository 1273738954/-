import { useNavigate } from "react-router-dom"
import PageHeader from "@/components/PageHeader"
import { cardShadow } from "@/components/Card"
import { Menu } from "lucide-react"

export default function More() {
  const navigate = useNavigate()

  return (
    <div className="animate-fadeUp">
      <PageHeader title="更多" subtitle="提前规划，少点纠结" icon={Menu} />

      <div className="px-5 py-4 max-w-[640px] mx-auto">
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
