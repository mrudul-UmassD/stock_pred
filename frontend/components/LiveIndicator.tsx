interface LiveIndicatorProps {
  isLive: boolean
}

export default function LiveIndicator({ isLive }: LiveIndicatorProps) {
  return (
    <div className="flex items-center gap-2">
      <div className={`w-2 h-2 rounded-full ${isLive ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
      <span className="text-sm font-medium">
        {isLive ? 'Live' : 'Static'}
      </span>
    </div>
  )
}
