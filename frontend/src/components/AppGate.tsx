import AchievementUnlockOverlay from "@/components/AchievementUnlockOverlay"

export default function AppGate({ children }: { children: React.ReactNode }) {
  return (
    <>
      {children}
      <AchievementUnlockOverlay />
    </>
  )
}
