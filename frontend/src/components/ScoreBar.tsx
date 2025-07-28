interface ScoreBarProps {
  score: number;
  className?: string;
}

export default function ScoreBar({ score, className = '' }: ScoreBarProps) {
  const percentage = Math.round(score * 100);
  
  const getColorClass = (score: number) => {
    if (score >= 0.8) return 'bg-green-500';
    if (score >= 0.6) return 'bg-yellow-500';
    if (score >= 0.4) return 'bg-orange-500';
    return 'bg-red-500';
  };

  return (
    <div className={`w-full ${className}`}>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-medium text-gray-600">Match Score</span>
        <span className="text-xs font-medium text-gray-900">{percentage}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div 
          className={`h-2 rounded-full transition-all duration-300 ${getColorClass(score)}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
