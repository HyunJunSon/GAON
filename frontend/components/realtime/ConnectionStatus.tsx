import { ConnectionStatus as Status } from '../../schemas/realtime'

interface ConnectionStatusProps {
  status: Status
  reconnectAttempts?: number
}

export const ConnectionStatus = ({ status, reconnectAttempts = 0 }: ConnectionStatusProps) => {
  const getStatusConfig = (status: Status) => {
    switch (status) {
      case 'connected':
        return {
          color: 'text-green-600',
          bgColor: 'bg-green-100',
          text: '연결됨',
          icon: '🟢'
        }
      case 'connecting':
        return {
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-100',
          text: '연결 중...',
          icon: '🟡'
        }
      case 'disconnected':
        return {
          color: 'text-gray-600',
          bgColor: 'bg-gray-100',
          text: '연결 끊김',
          icon: '⚪'
        }
      case 'error':
        return {
          color: 'text-red-600',
          bgColor: 'bg-red-100',
          text: '연결 오류',
          icon: '🔴'
        }
    }
  }

  const config = getStatusConfig(status)

  return (
    <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm ${config.bgColor} ${config.color}`}>
      <span className="mr-2">{config.icon}</span>
      <span>{config.text}</span>
      {reconnectAttempts > 0 && (
        <span className="ml-2 text-xs">
          (재연결 시도: {reconnectAttempts})
        </span>
      )}
    </div>
  )
}
