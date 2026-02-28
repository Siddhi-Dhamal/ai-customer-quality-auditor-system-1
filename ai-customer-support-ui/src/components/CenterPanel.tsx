import { Play, Search, Loader2 } from 'lucide-react';
import { useEffect, useState } from 'react';

interface Message {
  speaker: string;
  text: string;
  time: string;
}

function CenterPanel() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  // 🔥 Fetch transcript based on source type
  const fetchTranscript = async (source: "audio" | "text") => {
    setLoading(true);

    try {
      let endpoint = "";

      if (source === "audio") {
        endpoint = `http://localhost:8000/get-transcript?t=${Date.now()}`;
      } else {
        endpoint = `http://localhost:8001/get-text-transcript?t=${Date.now()}`;
      }

      const response = await fetch(endpoint);
      const data = await response.json();

      if (data && data.length > 0) {
        const formattedMessages = data.map((item: any) => ({
          speaker: item.speaker || "Speaker 00",
          text: item.text || item.transcription || "",
          time: item.start
            ? new Date(item.start * 1000).toISOString().substr(14, 5)
            : "00:00"
        }));

        setMessages(formattedMessages);
      } else {
        setMessages([]);
      }

    } catch (error) {
      console.error("Fetch error:", error);
      setMessages([]);
    } finally {
      setLoading(false);
    }
  };

  // 🔥 Listen for upload refresh event
  useEffect(() => {
    // Default load assumes audio
    fetchTranscript("audio");

    const handleRefresh = (event: any) => {
      const sourceType = event.detail || "audio";
      console.log("Refreshing transcript from:", sourceType);
      fetchTranscript(sourceType);
    };

    window.addEventListener("refreshTranscript", handleRefresh);
    return () => window.removeEventListener("refreshTranscript", handleRefresh);
  }, []);

  // 🔍 Search filter
  const filteredMessages = messages.filter(msg =>
    msg.text.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="flex-1 bg-gray-50 flex flex-col h-screen overflow-hidden">

      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-6 shadow-sm">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">
          Transcript
        </h2>

        {/* Audio Player UI (Visual Only) */}
        <div className="bg-slate-800 rounded-lg p-4 mb-4">
          <div className="flex items-center gap-4 mb-3">
            <button className="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-full transition-colors">
              <Play size={20} fill="white" />
            </button>

            <div className="flex-1 bg-slate-700 h-12 rounded-lg relative overflow-hidden flex items-center px-4">
              <div className="w-full bg-slate-600 h-1 rounded-full overflow-hidden">
                <div className="bg-blue-500 h-full w-1/3"></div>
              </div>
            </div>

            <span className="text-white text-sm font-mono">
              Real-time Audio
            </span>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <Search
            className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
            size={20}
          />
          <input
            type="text"
            placeholder="Search transcript..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-800"
          />
        </div>
      </div>

      {/* Transcript Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">

        {loading ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <Loader2 className="animate-spin mb-2" size={32} />
            <p className="animate-pulse">
              AI is processing...
            </p>
          </div>

        ) : filteredMessages.length > 0 ? (

          filteredMessages.map((message, index) => {
            const isAgent = message.speaker.includes("00");

            return (
              <div
                key={index}
                className={`flex ${isAgent ? "justify-start" : "justify-end"}`}
              >
                <div className="max-w-2xl">

                  <div className={`flex items-center gap-2 mb-1 ${isAgent ? "flex-row" : "flex-row-reverse"}`}>
                    <span className={`text-xs font-bold ${isAgent ? "text-blue-600" : "text-gray-600"}`}>
                      {isAgent
                        ? "Speaker 00 (Agent)"
                        : "Speaker 01 (Customer)"}
                    </span>
                    <span className="text-xs text-gray-400">
                      {message.time}
                    </span>
                  </div>

                  <div
                    className={`rounded-2xl px-4 py-3 shadow-sm ${
                      isAgent
                        ? "bg-blue-600 text-white rounded-tl-sm"
                        : "bg-gray-200 text-gray-800 rounded-tr-sm"
                    }`}
                  >
                    <p className="text-sm leading-relaxed">
                      {message.text}
                    </p>
                  </div>
                </div>
              </div>
            );
          })

        ) : (
          <div className="flex flex-col items-center justify-center h-full text-gray-400 border-2 border-dashed border-gray-200 rounded-2xl">
            <p className="text-lg font-medium">
              No active transcription
            </p>
            <p className="text-sm text-gray-300">
              Upload a file from the sidebar to begin.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default CenterPanel;