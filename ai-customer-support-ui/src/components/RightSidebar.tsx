import { CheckCircle2, Circle, Loader2, BarChart3, X, Heart, Shield, Target } from 'lucide-react';
import { useState, useEffect } from 'react';

const keywords = [
  'Account Access',
  'Authentication',
  'Password Reset',
  'Security',
  'Error Message',
  'Customer Support',
  'Resolution',
  'Login Issue',
];

const actionItems = [
  { id: '1', text: 'Follow up with customer in 24 hours', completed: false },
  { id: '2', text: 'Update account security documentation', completed: true },
  { id: '3', text: 'Log issue in tracking system', completed: true },
  { id: '4', text: 'Send satisfaction survey', completed: false },
];

function RightSidebar() {
  const [summary, setSummary] = useState<string>("Waiting for analysis...");
  const [loading, setLoading] = useState<boolean>(false);
  
  // 🔹 NEW STATES FOR QUALITY SCORING
  const [showDetails, setShowDetails] = useState(false);
  const [scores, setScores] = useState({ empathy: 0, compliance: 0, resolution: 0, reasoning: "" });

  const fetchTextSummary = async () => {
    try {
      const res = await fetch(`http://localhost:8001/get-text-summary?t=${Date.now()}`);
      const data = await res.json();
      setSummary(data.summary || "No summary found.");
    } catch (err) {
      setSummary("Error fetching text summary.");
    }
  };

  const fetchAudioSummary = async () => {
    try {
      const res = await fetch(`http://localhost:8000/get-summary?t=${Date.now()}`);
      const data = await res.json();
      setSummary(data.summary || "No summary found.");
    } catch (err) {
      setSummary("Error fetching audio summary.");
    }
  };

  // 🔹 NEW: FETCH SCORES FROM PORT 8002
  const fetchQualityScores = async () => {
    try {
      const res = await fetch("http://localhost:8002/get-quality-scores");
      if (res.ok) {
        const data = await res.json();
        setScores(data);
      }
    } catch (err) {
      console.error("Error fetching scores:", err);
    }
  };

  useEffect(() => {
    const handleRefresh = async (event: any) => {
      const type = event.detail;
      setLoading(true);
      if (type === "audio") {
        await fetchAudioSummary();
        await fetchQualityScores(); // Fetch scores when audio is refreshed
      } else if (type === "text") {
        await fetchTextSummary();
      }
      setLoading(false);
    };

    window.addEventListener("refreshTranscript", handleRefresh);
    return () => {
      window.removeEventListener("refreshTranscript", handleRefresh);
    };
  }, []);

  return (
    <div className="w-96 bg-slate-800 overflow-y-auto shadow-2xl h-screen border-l border-slate-700 flex flex-col relative">
      <div className="p-6 space-y-6">
        <h2 className="text-xl font-semibold text-white border-b border-slate-700 pb-4">
          AI Insights
        </h2>

        {/* Summary Section */}
        <div className="bg-slate-700 rounded-xl p-5 shadow-lg border border-slate-600 transition-all">
          <h3 className="text-xs font-bold text-slate-400 mb-3 uppercase tracking-widest">
            Executive Summary
          </h3>
          {loading ? (
            <div className="flex items-center gap-3 text-blue-400 py-4">
              <Loader2 className="animate-spin" size={20} />
              <span className="text-sm font-medium">Generating summary...</span>
            </div>
          ) : (
            <p className="text-sm text-slate-100 leading-relaxed italic border-l-2 border-blue-500 pl-4 py-1 whitespace-pre-line">
              {summary}
            </p>
          )}
        </div>

        {/* Sentiment Section - UPDATED WITH BUTTON */}
        <div className="bg-slate-700 rounded-xl p-5 shadow-lg border border-slate-600">
          <h3 className="text-xs font-bold text-slate-400 mb-4 uppercase tracking-widest">
            Customer Sentiment
          </h3>

          <div className="flex flex-col items-center">
            <div className="text-5xl mb-3">😊</div>
            <p className="text-2xl font-bold text-emerald-400 mb-2">85% Positive</p>

            <div className="w-full bg-slate-600 rounded-full h-2.5">
              <div
                className="bg-gradient-to-r from-emerald-500 to-teal-400 h-full rounded-full"
                style={{ width: '85%' }}
              />
            </div>

            <div className="flex justify-between w-full mt-2 text-[10px] text-slate-500 font-bold uppercase mb-4">
              <span>Negative</span>
              <span>Neutral</span>
              <span>Positive</span>
            </div>

            {/* 🔹 ADDED BUTTON */}
            <button 
              onClick={() => setShowDetails(true)}
              className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold flex items-center justify-center gap-2 transition-colors shadow-lg"
            >
              <BarChart3 size={14} />
              Detailed Analysis
            </button>
          </div>
        </div>

        {/* Keywords */}
        <div className="bg-slate-700 rounded-xl p-5 shadow-lg border border-slate-600">
          <h3 className="text-xs font-bold text-slate-400 mb-4 uppercase tracking-widest">
            Key Topics
          </h3>
          <div className="flex flex-wrap gap-2">
            {keywords.map((keyword, index) => (
              <span key={index} className="bg-blue-500/10 text-blue-300 border border-blue-500/20 px-3 py-1 rounded-md text-xs font-medium">
                {keyword}
              </span>
            ))}
          </div>
        </div>

        {/* Action Items */}
        <div className="bg-slate-700 rounded-xl p-5 shadow-lg border border-slate-600">
          <h3 className="text-xs font-bold text-slate-400 mb-4 uppercase tracking-widest">
            Next Steps
          </h3>
          <div className="space-y-4">
            {actionItems.map((item) => (
              <div key={item.id} className="flex items-start gap-3 group">
                {item.completed ? (
                  <CheckCircle2 size={18} className="text-emerald-500 mt-0.5 flex-shrink-0" />
                ) : (
                  <Circle size={18} className="text-slate-500 mt-0.5 flex-shrink-0" />
                )}
                <span className={`text-sm ${item.completed ? 'text-slate-500 line-through' : 'text-slate-200'}`}>
                  {item.text}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 🔹 FACTOR ANALYSIS MODAL OVERLAY */}
      {showDetails && (
        <div className="absolute inset-0 bg-slate-900/95 z-50 p-6 flex flex-col animate-in fade-in slide-in-from-right duration-300">
          <div className="flex justify-between items-center mb-8 border-b border-slate-800 pb-4">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <BarChart3 className="text-blue-400" />
              Factor Analysis
            </h3>
            <button onClick={() => setShowDetails(false)} className="text-slate-400 hover:text-white transition-colors">
              <X size={24} />
            </button>
          </div>

          <div className="space-y-8 flex-1 overflow-y-auto pr-2 custom-scrollbar">
            {[
              { label: 'Empathy', val: scores.empathy, color: 'bg-blue-500', icon: <Heart size={16}/> },
              { label: 'Compliance', val: scores.compliance, color: 'bg-emerald-500', icon: <Shield size={16}/> },
              { label: 'Resolution', val: scores.resolution, color: 'bg-purple-500', icon: <Target size={16}/> }
            ].map((factor) => (
              <div key={factor.label} className="space-y-3">
                <div className="flex justify-between items-end">
                  <div className="flex items-center gap-2 text-slate-300">
                    {factor.icon}
                    <span className="text-xs font-bold uppercase tracking-wider">{factor.label}</span>
                  </div>
                  <span className="text-xl font-black text-white">{factor.val}<span className="text-xs text-slate-500">/10</span></span>
                </div>
                <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
                  <div 
                    className={`${factor.color} h-full rounded-full transition-all duration-1000 ease-out shadow-[0_0_10px_rgba(59,130,246,0.5)]`}
                    style={{ width: `${factor.val * 10}%` }}
                  />
                </div>
              </div>
            ))}

            <div className="mt-8 p-4 bg-slate-800/50 rounded-xl border border-slate-700">
              <h4 className="text-[10px] font-bold text-slate-500 uppercase mb-2 tracking-widest">Auditor Reasoning</h4>
              <p className="text-xs text-slate-300 italic leading-relaxed">
                {scores.reasoning || "Analysis results will appear here after a call is processed."}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default RightSidebar;
