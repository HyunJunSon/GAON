interface UserInfo {
  user_id: number
  user_name: string
}

interface UserListProps {
  users: UserInfo[]
  currentUserId: number
}

export const UserList = ({ users, currentUserId }: UserListProps) => {
  if (users.length === 0) {
    return null
  }

  return (
    <div className="bg-gray-50 p-3 border-b">
      <h3 className="text-sm font-medium text-gray-700 mb-2">
        참여자 ({users.length}명)
      </h3>
      <div className="flex flex-wrap gap-2">
        {users.map((user) => (
          <span
            key={user.user_id}
            className={`inline-flex items-center px-2 py-1 rounded-full text-xs ${
              user.user_id === currentUserId
                ? 'bg-blue-100 text-blue-800'
                : 'bg-gray-200 text-gray-700'
            }`}
          >
            <span className="w-2 h-2 bg-green-400 rounded-full mr-1"></span>
            {user.user_id === currentUserId ? '나' : user.user_name}
          </span>
        ))}
      </div>
    </div>
  )
}
