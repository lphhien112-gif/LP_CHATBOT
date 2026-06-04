import MessageBubble from './MessageBubble'

export default function MessageList({ messages, onSuggestion, isWaiting }) {
  return (
    <div className="space-y-5">
      {messages.map((m) => (
        <MessageBubble key={m.id} message={m} onSuggestion={onSuggestion} isWaiting={isWaiting} />
      ))}
    </div>
  )
}
