import { useState } from "react"
import { createPortal } from "react-dom"
import { useNavigate } from "react-router-dom"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { recordsApi, dayRatingApi, uploadApi, getUploadErrorMessage } from "@/api"
import { useAuthStore } from "@/store/useAuthStore"
import type { MealRecord, DayRating } from "@/types"
import PhotoViewer from "@/components/PhotoViewer"
import SwipeDeleteRow from "@/components/SwipeDeleteRow"
import { cardShadow } from "@/components/Card"
import toast from "react-hot-toast"

const moodOptions = [
  { key: "yum", emoji: "😋", label: "好吃" },
  { key: "ok", emoji: "😐", label: "一般" },
  { key: "no", emoji: "😵", label: "不想再吃" },
]

const mealMoodOptions = [
  { key: "great", emoji: "😋", label: "超满足" },
  { key: "ok", emoji: "😐", label: "还行吧" },
  { key: "meh", emoji: "😕", label: "不太行" },
]

const moodEmojiMap: Record<string, string> = { yum: "😋", ok: "😐", no: "😵", great: "😋", meh: "😕" }

function todayKey() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`
}

function parsePhotos(photosStr: string): string[] {
  try {
    const arr = JSON.parse(photosStr)
    return Array.isArray(arr) ? arr : []
  } catch {
    return []
  }
}

export default function TodayMealCard() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const isAdminLoggedIn = useAuthStore((s) => s.isLoggedIn)
  const dateKey = todayKey()

  const [ratingRecord, setRatingRecord] = useState<MealRecord | null>(null)
  const [ratingMood, setRatingMood] = useState<string>("")
  const [ratingRemark, setRatingRemark] = useState("")
  const [ratingPhoto, setRatingPhoto] = useState("")
  const [showMealRating, setShowMealRating] = useState(false)
  const [mealRatingMood, setMealRatingMood] = useState<string>("")
  const [mealRatingRemark, setMealRatingRemark] = useState("")
  const [mealPhotos, setMealPhotos] = useState<string[]>([])
  const [viewerPhotos, setViewerPhotos] = useState<string[]>([])
  const [viewerIdx, setViewerIdx] = useState(0)
  const [showViewer, setShowViewer] = useState(false)

  const { data: recordsData } = useQuery({
    queryKey: ["records", "today-card", dateKey],
    queryFn: () => recordsApi.list({ date_from: dateKey, date_to: dateKey, pageSize: "100" }),
  })

  const { data: dayRatingData } = useQuery({
    queryKey: ["day-rating", dateKey],
    queryFn: () => dayRatingApi.get(dateKey),
  })
  const dayRating = (dayRatingData as DayRating | null) || null

  const records = recordsData?.items || []

  const deleteMut = useMutation({
    mutationFn: (id: number) => recordsApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["records"] })
      qc.invalidateQueries({ queryKey: ["stats"] })
      qc.invalidateQueries({ queryKey: ["achievements"] })
      toast.success("已删除")
    },
    onError: () => toast.error("删除失败"),
  })

  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<MealRecord> }) => recordsApi.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["records"] })
      qc.invalidateQueries({ queryKey: ["achievements"] })
      toast.success("评价已保存")
      setRatingRecord(null)
    },
    onError: () => toast.error("评价失败"),
  })

  const dayRatingMut = useMutation({
    mutationFn: (data: { meal_date: string; mood: string; remark?: string; photos?: string }) =>
      dayRatingApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["day-rating"] })
      qc.invalidateQueries({ queryKey: ["day-ratings"] })
      qc.invalidateQueries({ queryKey: ["photo-wall"] })
      qc.invalidateQueries({ queryKey: ["achievements"] })
      toast.success("今日评价已保存")
      setShowMealRating(false)
    },
    onError: () => toast.error("评价保存失败"),
  })

  const updateDayPhotosMut = useMutation({
    mutationFn: (data: { meal_date: string; photos: string }) => dayRatingApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["day-rating", dateKey] })
      qc.invalidateQueries({ queryKey: ["day-ratings"] })
      qc.invalidateQueries({ queryKey: ["photo-wall"] })
      toast.success("照片已删除")
    },
    onError: () => toast.error("照片删除失败"),
  })

  function openRating(r: MealRecord) {
    setRatingRecord(r)
    setRatingMood(r.mood || "")
    setRatingRemark(r.remark || "")
    setRatingPhoto(r.photo || "")
  }

  function submitRating() {
    if (!ratingRecord) return
    updateMut.mutate({ id: ratingRecord.id, data: { mood: ratingMood, remark: ratingRemark, photo: ratingPhoto } })
  }

  function openMealRating() {
    setMealRatingMood(dayRating?.mood || "")
    setMealRatingRemark(dayRating?.remark || "")
    setMealPhotos(dayRating?.photos ? parsePhotos(dayRating.photos) : [])
    setShowMealRating(true)
  }

  function submitMealRating() {
    if (!mealRatingMood) return
    dayRatingMut.mutate({
      meal_date: dateKey,
      mood: mealRatingMood,
      remark: mealRatingRemark,
      photos: JSON.stringify(mealPhotos),
    })
  }

  async function handleRatingPhotoUpload() {
    if (!isAdminLoggedIn) {
      toast.error("上传照片需要先进入管理模式")
      navigate("/admin/login")
      return
    }
    const input = document.createElement("input")
    input.type = "file"
    input.accept = "image/jpg,image/jpeg,image/png,image/webp"
    input.onchange = async () => {
      const file = input.files?.[0]
      if (!file) return
      try {
        const res = await uploadApi.image(file)
        const url = res.data.data.url
        if (url) setRatingPhoto(url)
        else toast.error("上传返回异常")
      } catch (err) {
        toast.error(getUploadErrorMessage(err))
      }
    }
    input.click()
  }

  async function handlePhotoUpload() {
    if (!isAdminLoggedIn) {
      toast.error("上传照片需要先进入管理模式")
      navigate("/admin/login")
      return
    }
    const input = document.createElement("input")
    input.type = "file"
    input.multiple = true
    input.accept = "image/jpg,image/jpeg,image/png,image/webp"
    input.onchange = async () => {
      const files = Array.from(input.files || [])
      if (files.length === 0) return
      const remaining = 9 - mealPhotos.length
      if (remaining <= 0) {
        toast.error("最多上传9张照片")
        return
      }
      const toUpload = files.slice(0, remaining)
      if (files.length > remaining) toast.error(`已选${files.length}张，仅上传前${remaining}张`)
      let failed = 0
      let lastErrMsg = ""
      for (const file of toUpload) {
        try {
          const res = await uploadApi.image(file)
          const url = res.data.data.url
          if (url) setMealPhotos((prev) => [...prev, url])
          else failed++
        } catch (err) {
          failed++
          lastErrMsg = getUploadErrorMessage(err)
        }
      }
      if (failed > 0) toast.error(lastErrMsg || `${failed}张上传失败`)
    }
    input.click()
  }

  function removeMealPhoto(idx: number) {
    setMealPhotos((prev) => prev.filter((_, i) => i !== idx))
  }

  function removeDayPhoto(idx: number) {
    if (!isAdminLoggedIn) {
      toast.error("删除照片需要先进入管理模式")
      navigate("/admin/login")
      return
    }
    const dayPhotos = dayRating?.photos ? parsePhotos(dayRating.photos) : []
    updateDayPhotosMut.mutate({ meal_date: dateKey, photos: JSON.stringify(dayPhotos.filter((_, i) => i !== idx)) })
  }

  function openViewer(photos: string[], idx: number) {
    setViewerPhotos(photos)
    setViewerIdx(idx)
    setShowViewer(true)
  }

  const dayPhotos = dayRating?.photos ? parsePhotos(dayRating.photos) : []
  const hasPhotos = dayPhotos.length > 0
  const d = new Date()

  return (
    <>
      <div className={`bg-card rounded-2xl overflow-hidden ${cardShadow} border border-border mb-5`}>
        <div className="px-4 py-3 bg-primary-light text-sm font-semibold text-primary flex items-center justify-between">
          <div className="flex items-center gap-1.5 flex-wrap">
            {d.getMonth() + 1}月{d.getDate()}日
            <span className="text-[10px] font-medium bg-primary text-white px-1.5 py-px rounded-full">今天</span>
          </div>
          <button
            onClick={openMealRating}
            className={`px-2.5 py-0.5 rounded-full text-[11px] font-semibold transition-all active:scale-95 ${dayRating?.mood ? "bg-mint text-white" : "bg-primary text-white"}`}
          >
            {dayRating?.mood ? "✓ 已评价" : "😌 评价"}
          </button>
        </div>

        {records.length === 0 ? (
          <div className="py-6 px-4 text-center text-[13px] text-text3">今天还没有记录哦~</div>
        ) : (
          records.map((r) => (
            <SwipeDeleteRow key={r.id} actionWidth={80} onDelete={() => deleteMut.mutate(r.id)} className="bg-red">
              <div className="flex items-center gap-3 px-4 py-3 border-b border-border last:border-0 transition-all active:bg-bg w-full text-left cursor-pointer">
                <span onClick={() => navigate(`/dishes/${r.dish_id}`)} className={`w-10 h-10 rounded-[10px] flex items-center justify-center text-xl flex-shrink-0 overflow-hidden ${r.meal_type === "lunch" ? "bg-primary-light" : "bg-mint-light"}`}>
                  {r.dish_image_url ? <img src={r.dish_image_url} alt={r.dish_name} className="w-full h-full object-cover" /> : r.dish_emoji}
                </span>
                <div className="flex-1 min-w-0" onClick={() => navigate(`/dishes/${r.dish_id}`)}>
                  <div className="text-sm font-semibold mb-px">{r.dish_name}</div>
                  <div className="text-[11px] text-text2">{r.meal_type === "lunch" ? "午餐" : "晚餐"}</div>
                </div>
                {r.mood ? (
                  <div onClick={(e) => { e.stopPropagation(); openRating(r) }} className="flex-shrink-0 flex items-center gap-1 cursor-pointer active:scale-95 transition-transform">
                    <span className="text-lg">{moodEmojiMap[r.mood]}</span>
                    {r.remark && <span className="text-[11px] text-text2 max-w-[60px] truncate">{r.remark}</span>}
                  </div>
                ) : (
                  <button onClick={(e) => { e.stopPropagation(); openRating(r) }} className="flex-shrink-0 px-2 py-1 rounded-full text-[10px] font-medium bg-primary-light text-primary active:scale-95 transition-all">评价</button>
                )}
              </div>
            </SwipeDeleteRow>
          ))
        )}

        {dayRating?.mood && (
          <div className="px-4 py-2.5 bg-bg border-t border-border flex items-center gap-2.5 text-[13px]">
            <span className="text-xl">🍚</span>
            <span className="flex-1 text-text2">
              {records.length > 1 ? "午餐+晚餐" : "一餐"} · 整体评价
              {dayRating.remark && <span className="ml-1 text-text"> {dayRating.remark}</span>}
            </span>
            <span className="text-xl">{moodEmojiMap[dayRating.mood] || "😋"}</span>
          </div>
        )}

        <div className="px-4 py-2.5 border-t border-border">
          <div className="text-[11px] text-text3 mb-1.5">{hasPhotos ? `📷 照片 (${dayPhotos.length})` : "📷 拍张照记录一下？"}</div>
          <div className="flex gap-1.5 overflow-x-auto scrollbar-none pb-1">
            {dayPhotos.map((p, i) => (
              <div
                key={i}
                className="w-14 h-14 rounded-md overflow-hidden flex-shrink-0 bg-bg border border-border flex items-center justify-center cursor-pointer transition-all active:scale-95 relative"
                onClick={() => openViewer(dayPhotos, i)}
              >
                <img src={p} alt="" className="w-full h-full object-cover" />
                {isAdminLoggedIn && (
                  <button
                    onClick={(e) => { e.stopPropagation(); removeDayPhoto(i) }}
                    className="absolute top-0 right-0 w-[16px] h-[16px] rounded-bl-md bg-black/50 text-white text-[9px] flex items-center justify-center active:bg-red"
                  >✕</button>
                )}
              </div>
            ))}
            <div
              onClick={openMealRating}
              className="w-14 h-14 rounded-md flex-shrink-0 border-2 border-dashed border-border2 flex flex-col items-center justify-center cursor-pointer transition-all active:border-primary active:text-primary text-text3"
            >
              <span className="text-base leading-none">+</span>
              <span className="text-[9px]">添加</span>
            </div>
          </div>
        </div>
      </div>

      {ratingRecord && createPortal(
        <div className="fixed inset-0 z-[400] bg-black/45 backdrop-blur-sm flex items-end justify-center" onClick={() => setRatingRecord(null)}>
          <div className="bg-card w-full max-w-[640px] rounded-t-2xl animate-slide-in-up" onClick={(e) => e.stopPropagation()}>
            <div className="w-9 h-1 rounded-full bg-border2 mx-auto mt-2" />
            <div className="px-5 py-4 border-b border-border flex items-center justify-between">
              <div className="text-base font-bold">{ratingRecord.dish_name} — 这道菜怎么样？</div>
              <button onClick={() => setRatingRecord(null)} className="w-7 h-7 rounded-full flex items-center justify-center text-text3 hover:bg-bg text-sm">✕</button>
            </div>
            <div className="p-5">
              <div className="flex justify-center gap-4 mb-5">
                {moodOptions.map((m) => (
                  <button
                    key={m.key}
                    onClick={() => setRatingMood(m.key)}
                    className={`flex flex-col items-center gap-1.5 p-3 px-5 rounded-2xl border-2 transition-all active:scale-90 ${ratingMood === m.key ? "border-primary bg-primary-light" : "border-transparent bg-bg"}`}
                  >
                    <span className="text-3xl">{m.emoji}</span>
                    <span className={`text-xs font-medium ${ratingMood === m.key ? "text-primary" : "text-text2"}`}>{m.label}</span>
                  </button>
                ))}
              </div>
              <div className="mb-5">
                <div className="text-xs text-text2 font-semibold mb-2">备注（可选）</div>
                <textarea
                  value={ratingRemark}
                  onChange={(e) => setRatingRemark(e.target.value)}
                  placeholder="这道菜怎么样..."
                  rows={2}
                  className="w-full p-3 rounded-[10px] border-[1.5px] border-border bg-bg text-sm resize-none focus:border-primary focus:ring-2 focus:ring-primary/10 outline-none transition-all"
                />
              </div>
              <div className="mb-5">
                <div className="text-xs text-text2 font-semibold mb-2">📷 成品照（可选，限1张）</div>
                {ratingPhoto ? (
                  <div className="relative w-20 h-20 rounded-[10px] overflow-hidden border border-border">
                    <img src={ratingPhoto} alt="" className="w-full h-full object-cover" />
                    <button onClick={() => setRatingPhoto("")} className="absolute top-0.5 right-0.5 w-[18px] h-[18px] rounded-full bg-black/50 text-white text-[10px] flex items-center justify-center">✕</button>
                  </div>
                ) : (
                  <div
                    onClick={handleRatingPhotoUpload}
                    className={`w-20 h-20 rounded-[10px] border-2 border-dashed border-border2 flex flex-col items-center justify-center cursor-pointer transition-all active:border-primary active:text-primary ${isAdminLoggedIn ? "text-text3" : "text-text4 bg-bg/60"}`}
                  >
                    <span className="text-xl leading-none">+</span>
                    <span className="text-[9px]">添加</span>
                  </div>
                )}
              </div>
              <button
                onClick={submitRating}
                disabled={!ratingMood}
                className="w-full py-3 rounded-full text-sm font-semibold bg-primary text-white transition-all active:scale-96 disabled:opacity-40 disabled:active:scale-100"
              >保存评价</button>
            </div>
          </div>
        </div>,
        document.body
      )}

      {showMealRating && createPortal(
        <div className="fixed inset-0 z-[400] bg-black/45 backdrop-blur-sm flex items-end justify-center" onClick={() => setShowMealRating(false)}>
          <div className="bg-card w-full max-w-[640px] rounded-t-2xl animate-slide-in-up" onClick={(e) => e.stopPropagation()}>
            <div className="w-9 h-1 rounded-full bg-border2 mx-auto mt-2" />
            <div className="px-5 py-4 border-b border-border flex items-center justify-between">
              <div className="text-base font-bold">🍲 这顿饭怎么样？</div>
              <button onClick={() => setShowMealRating(false)} className="w-7 h-7 rounded-full flex items-center justify-center text-text3 hover:bg-bg text-sm">✕</button>
            </div>
            <div className="p-5">
              <div className="text-center mb-3 text-[13px] text-text2">评价今天整体的用餐感受</div>
              <div className="flex justify-center gap-4 mb-5">
                {mealMoodOptions.map((m) => (
                  <button
                    key={m.key}
                    onClick={() => setMealRatingMood(m.key)}
                    className={`flex flex-col items-center gap-1.5 p-3 px-5 rounded-2xl border-2 transition-all active:scale-90 ${mealRatingMood === m.key ? "border-primary bg-primary-light" : "border-transparent bg-bg"}`}
                  >
                    <span className="text-3xl">{m.emoji}</span>
                    <span className={`text-xs font-medium ${mealRatingMood === m.key ? "text-primary" : "text-text2"}`}>{m.label}</span>
                  </button>
                ))}
              </div>
              <div className="mb-5">
                <div className="text-xs text-text2 font-semibold mb-2">备注（可选）</div>
                <textarea
                  value={mealRatingRemark}
                  onChange={(e) => setMealRatingRemark(e.target.value)}
                  placeholder="今天这顿饭的整体感受..."
                  rows={2}
                  className="w-full p-3 rounded-[10px] border-[1.5px] border-border bg-bg text-sm resize-none focus:border-primary focus:ring-2 focus:ring-primary/10 outline-none transition-all"
                />
              </div>
              <div className="mb-5">
                <div className="text-xs text-text2 font-semibold mb-2">📷 上传照片（可选，最多9张）</div>
                <div className="flex gap-2 items-start">
                  <div
                    onClick={handlePhotoUpload}
                    className={`w-16 h-16 rounded-[10px] border-2 border-dashed border-border2 flex flex-col items-center justify-center cursor-pointer transition-all active:border-primary active:text-primary flex-shrink-0 ${isAdminLoggedIn ? "text-text3" : "text-text4 bg-bg/60"}`}
                  >
                    <span className="text-xl leading-none">+</span>
                    <span className="text-[9px]">添加</span>
                  </div>
                  <div className="flex gap-2 flex-wrap">
                    {mealPhotos.map((p, i) => (
                      <div key={i} className="w-16 h-16 rounded-[10px] overflow-hidden relative bg-bg flex items-center justify-center border border-border">
                        <img src={p} alt="" className="w-full h-full object-cover" />
                        <button
                          onClick={(e) => { e.stopPropagation(); removeMealPhoto(i) }}
                          className="absolute top-0.5 right-0.5 w-[18px] h-[18px] rounded-full bg-black/50 text-white text-[10px] flex items-center justify-center active:bg-red"
                        >✕</button>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              <button
                onClick={submitMealRating}
                disabled={!mealRatingMood}
                className="w-full py-3 rounded-full text-sm font-semibold bg-primary text-white transition-all active:scale-96 disabled:opacity-40 disabled:active:scale-100"
              >保存评价</button>
            </div>
          </div>
        </div>,
        document.body
      )}

      {showViewer && viewerPhotos.length > 0 && createPortal(
        <PhotoViewer photos={viewerPhotos} idx={viewerIdx} setIdx={setViewerIdx} onClose={() => setShowViewer(false)} />,
        document.body
      )}
    </>
  )
}
