import { useState } from 'react';
import { toast } from 'react-hot-toast';
import useChatStore from '../store/useChatStore';
import { startConsultation } from '../services/api';
import ChatInterface from '../components/ChatInterface';

const Home = () => {
  const [query, setQuery] = useState('');
  const [sessionStarted, setSessionStarted] = useState(false);
  const [showConsultation, setShowConsultation] = useState(false);
  const [isFinal, setIsFinal] = useState(false);
  const [finalReport, setFinalReport] = useState(null);

  const {
    startSession,
    addMessage,
    setPartialReport,
    setLoading,
  } = useChatStore();

  const handleStartConsultation = async () => {
    if (!query.trim()) {
      toast.error('Please enter your legal query');
      return;
    }

    setLoading(true);

    try {
      const cleaned = query.trim();
      const response = await startConsultation(cleaned);

      console.log('Initial consultation response:', response);

      startSession(response.session_id);
      addMessage('user', cleaned);
      setSessionStarted(true);

      if (response.partial_report) {
        setPartialReport(response.partial_report);
      }

      if (response.question) {
        addMessage('bot', response.question);
      }

      if (response.next_action === 'final') {
        setIsFinal(true);
        setFinalReport(response.partial_report || response.final_report);
      }

      setLoading(false);
      toast.success('Consultation started!');
    } catch (error) {
      setLoading(false);
      toast.error(`Failed to start consultation: ${error?.message || 'Please try again.'}`);
    }
  };

  if (sessionStarted) {
    return (
      <div className="container mx-auto px-4 py-8 h-screen flex flex-col">
        <ChatInterface isFinal={isFinal} finalReport={finalReport} />
      </div>
    );
  }

  if (showConsultation) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Navigation */}
        <nav className="bg-white shadow-sm border-b border-gray-200">
          <div className="container mx-auto px-6 py-4 flex justify-between items-center">
            <div className="text-2xl font-bold text-blue-600">Chatlaw</div>
            <div className="flex gap-4">
              <button
                onClick={() => setShowConsultation(false)}
                className="px-4 py-2 text-gray-700 hover:text-blue-600 transition-colors"
              >
                ← Back
              </button>
              <button className="px-4 py-2 text-gray-700 hover:text-blue-600 transition-colors">
                Login
              </button>
              <button className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                Sign Up
              </button>
            </div>
          </div>
        </nav>

        {/* Consultation Form */}
        <div className="container mx-auto px-4 py-16">
          <div className="max-w-3xl mx-auto">
            <h1 className="text-4xl font-bold text-gray-800 mb-4 text-center">
              Start Your Legal Consultation
            </h1>
            <p className="text-gray-600 text-center mb-8">
              Describe your legal question and get expert AI-powered guidance
            </p>

            <div className="bg-white rounded-xl shadow-lg p-8 border border-gray-100">
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Describe your legal question or situation in detail..."
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none mb-6"
                rows={10}
              />

              <button
                onClick={handleStartConsultation}
                className="w-full px-6 py-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white text-lg font-semibold rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
              >
                Start Consultation
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Navigation */}
      <nav className="bg-white/80 backdrop-blur-sm shadow-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4 flex justify-between items-center">
          <div className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Chatlaw
          </div>
          <div className="flex gap-4">
            <button className="px-4 py-2 text-gray-700 hover:text-blue-600 transition-colors font-medium">
              Login
            </button>
            <button className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium shadow-md">
              Sign Up
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="container mx-auto px-6 py-20 text-center">
        <h1 className="text-6xl font-bold text-gray-900 mb-6 leading-tight">
          Your AI Legal Assistant
          <span className="block text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">
            Powered by Multi-Agent Intelligence
          </span>
        </h1>
        <p className="text-xl text-gray-600 mb-12 max-w-3xl mx-auto">
          Get instant, expert legal guidance from our advanced AI system with
          multiple specialized agents working together to provide comprehensive
          legal analysis and recommendations.
        </p>
        <button
          onClick={() => setShowConsultation(true)}
          className="px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white text-lg font-semibold rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all shadow-xl hover:shadow-2xl transform hover:-translate-y-1"
        >
          Start Free Consultation →
        </button>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-6 py-20">
        <h2 className="text-4xl font-bold text-center text-gray-900 mb-16">
          Why Choose Chatlaw?
        </h2>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {/* Feature 1 */}
          <div className="bg-white rounded-xl p-8 shadow-lg hover:shadow-2xl transition-all transform hover:-translate-y-2 border border-gray-100">
            <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center mb-4">
              <svg
                className="w-8 h-8 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                />
              </svg>
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-3">
              Multi-Agent AI System
            </h3>
            <p className="text-gray-600 leading-relaxed">
              Four specialized AI agents—Legal Assistant, Researcher, Editor,
              and Senior Lawyer—work in harmony to deliver comprehensive legal
              analysis with unmatched accuracy.
            </p>
          </div>

          {/* Feature 2 */}
          <div className="bg-white rounded-xl p-8 shadow-lg hover:shadow-2xl transition-all transform hover:-translate-y-2 border border-gray-100">
            <div className="w-14 h-14 bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg flex items-center justify-center mb-4">
              <svg
                className="w-8 h-8 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-3">
              Instant Responses
            </h3>
            <p className="text-gray-600 leading-relaxed">
              Get real-time legal guidance without waiting hours or days. Our AI
              system processes your queries instantly and provides detailed,
              actionable advice.
            </p>
          </div>

          {/* Feature 3 */}
          <div className="bg-white rounded-xl p-8 shadow-lg hover:shadow-2xl transition-all transform hover:-translate-y-2 border border-gray-100">
            <div className="w-14 h-14 bg-gradient-to-br from-green-500 to-green-600 rounded-lg flex items-center justify-center mb-4">
              <svg
                className="w-8 h-8 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                />
              </svg>
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-3">
              Comprehensive Analysis
            </h3>
            <p className="text-gray-600 leading-relaxed">
              Receive detailed legal reports with case analysis, relevant
              precedents, and professional recommendations tailored to your
              specific situation.
            </p>
          </div>

          {/* Feature 4 */}
          <div className="bg-white rounded-xl p-8 shadow-lg hover:shadow-2xl transition-all transform hover:-translate-y-2 border border-gray-100">
            <div className="w-14 h-14 bg-gradient-to-br from-orange-500 to-orange-600 rounded-lg flex items-center justify-center mb-4">
              <svg
                className="w-8 h-8 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                />
              </svg>
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-3">
              Secure & Private
            </h3>
            <p className="text-gray-600 leading-relaxed">
              Your legal information is encrypted and kept completely
              confidential. We prioritize your privacy and data security above
              all else.
            </p>
          </div>

          {/* Feature 5 */}
          <div className="bg-white rounded-xl p-8 shadow-lg hover:shadow-2xl transition-all transform hover:-translate-y-2 border border-gray-100">
            <div className="w-14 h-14 bg-gradient-to-br from-pink-500 to-pink-600 rounded-lg flex items-center justify-center mb-4">
              <svg
                className="w-8 h-8 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                />
              </svg>
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-3">
              Interactive Consultation
            </h3>
            <p className="text-gray-600 leading-relaxed">
              Engage in a natural conversation with our AI. Ask follow-up
              questions, clarify doubts, and get step-by-step guidance through
              your legal journey.
            </p>
          </div>

          {/* Feature 6 */}
          <div className="bg-white rounded-xl p-8 shadow-lg hover:shadow-2xl transition-all transform hover:-translate-y-2 border border-gray-100">
            <div className="w-14 h-14 bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-lg flex items-center justify-center mb-4">
              <svg
                className="w-8 h-8 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-3">
              Detailed Reports
            </h3>
            <p className="text-gray-600 leading-relaxed">
              Download comprehensive legal reports with citations, case
              references, and actionable recommendations—all formatted
              professionally for your records.
            </p>
          </div>
        </div>
      </section>

      {/* Consultation CTA Section */}
      <section className="container mx-auto px-6 py-20">
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-12 text-center text-white shadow-2xl">
          <h2 className="text-4xl font-bold mb-4">Ready to Get Started?</h2>
          <p className="text-xl mb-8 text-blue-100">
            Start your free consultation now and experience the power of AI-driven
            legal assistance.
          </p>
          <button
            onClick={() => setShowConsultation(true)}
            className="px-8 py-4 bg-white text-blue-600 text-lg font-semibold rounded-lg hover:bg-gray-100 transition-all shadow-xl hover:shadow-2xl transform hover:-translate-y-1"
          >
            Begin Consultation Now →
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-12">
        <div className="container mx-auto px-6 text-center">
          <p className="text-lg mb-2">© 2024 Chatlaw. All rights reserved.</p>
          <p className="text-sm">AI-Powered Legal Assistance</p>
        </div>
      </footer>
    </div>
  );
};

export default Home;
