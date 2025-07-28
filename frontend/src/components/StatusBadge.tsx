import { CheckCircle, XCircle } from 'lucide-react';

interface StatusBadgeProps {
  status: 'approved' | 'disqualified';
  className?: string;
}

export default function StatusBadge({ status, className = '' }: StatusBadgeProps) {
  const isApproved = status === 'approved';
  
  return (
    <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium ${
      isApproved 
        ? 'bg-green-100 text-green-700' 
        : 'bg-red-100 text-red-700'
    } ${className}`}>
      {isApproved ? (
        <CheckCircle className="w-3 h-3" />
      ) : (
        <XCircle className="w-3 h-3" />
      )}
      {status}
    </div>
  );
}
