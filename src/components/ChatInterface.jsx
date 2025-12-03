import { useState, useEffect, useRef } from 'react';
import { toast } from 'react-hot-toast';
import useChatStore from '../store/useChatStore';
import { sendAnswer } from '../services/api';
import MessageBubble from './MessageBubble';
// import PartialReportCard from './PartialReportCard';
import FinalReport from './FinalReport';

const ChatInterface = ({ isFinal: initialIsFinal, finalReport: initialFinalReport }) => {
  const {
    sessionId,
    messages,
    partialReport,
    isLoading,
    questionCount,
    addMessage,
    setPartialReport,
    setLoading,
  } = useChatStore();

  const [inputText, setInputText] = useState('');
  const [isFinal, setIsFinal] = useState(initialIsFinal || false);
  const [finalReport, setFinalReport] = useState(initialFinalReport || null);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (initialIsFinal) {
      setIsFinal(true);
      setFinalReport(initialFinalReport);
    }
  }, [initialIsFinal, initialFinalReport]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!inputText.trim() || isLoading) return;

    const userMessage = inputText.trim();
    setInputText('');
    addMessage('user', userMessage);

    setLoading(true);

    try {
      const response = await sendAnswer(sessionId, userMessage);

      console.log('=== RESPONSE DEBUG ===');
      console.log('Question count before:', questionCount);
      console.log('Backend response:', response);
      console.log('Current messages:', messages);
      console.log('====================');

      // Don't show partial report during questioning
      // if (response.partial_report) {
      //   setPartialReport(response.partial_report);
      // }

      // Always add the question - the backend determines the flow
      if (response.question) {
        addMessage('bot', response.question);
      }

      // Check if this is the final report
      // Final response has 'report' field OR next_action === 'final' OR no next_action field
      if (response.next_action === 'final' || response.report || (!response.next_action && !response.question)) {
        // Show generating report message
        setIsGeneratingReport(true);
        addMessage('bot', '📄 Generating your comprehensive legal report...');
        
        // Small delay to show the message, then display report
        setTimeout(() => {
          setIsFinal(true);
          // Backend sends 'report' for final, not 'partial_report'
          setFinalReport(response.report || response.partial_report || response.final_report);
          setIsGeneratingReport(false);
        }, 1500);
      }

      setLoading(false);
    } catch (error) {
      console.error('Error in handleSend:', error);
      setLoading(false);
      toast.error('Failed to send message. Please try again.');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (isFinal) {
    return (
      <div className="flex flex-col h-full">
        <FinalReport report={finalReport || partialReport} />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Don't show partial report during questioning */}
      {/* <PartialReportCard report={partialReport} /> */}

      <div className="flex-1 overflow-y-auto mb-4 p-4 space-y-2">
        {messages.map((message, index) => (
          <MessageBubble
            key={index}
            role={message.role}
            text={message.text}
          />
        ))}
        
        {/* Loading animation when waiting for response */}
        {isLoading && (
          <div className="flex items-start gap-2 animate-fade-in">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-semibold">
              AI
            </div>
            <div className="bg-gray-100 rounded-lg p-3 max-w-[70%]">
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
                <span className="text-sm text-gray-600">
                  {isGeneratingReport ? '🤖 AI is analyzing your case and preparing report...' : 
                   messages.length <= 2 ? 'Analyzing your case...' : 'Processing your answer...'}
                </span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-gray-300 p-4">
        <div className="flex gap-2">
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your answer..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            rows={2}
            disabled={isLoading}
          />
          <button
            onClick={handleSend}
            disabled={isLoading || !inputText.trim()}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;

