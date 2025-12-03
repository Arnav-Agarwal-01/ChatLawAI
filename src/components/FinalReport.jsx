const FinalReport = ({ report }) => {
  const handleDownload = () => {
    console.log('Download report:', report);
  };

  const renderReport = () => {
    if (typeof report === 'string') {
      return <pre className="whitespace-pre-wrap text-sm">{report}</pre>;
    }

    if (typeof report === 'object' && report !== null) {
      return (
        <div className="space-y-2">
          {Object.entries(report).map(([key, value]) => (
            <div key={key} className="border-b border-gray-200 pb-2">
              <strong className="text-gray-700">{key}:</strong>
              <p className="text-gray-600 mt-1 whitespace-pre-wrap">
                {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
              </p>
            </div>
          ))}
        </div>
      );
    }

    return <p className="text-gray-600">No report available</p>;
  };

  return (
    <div className="p-6 bg-white border border-gray-300 rounded-lg shadow-md mb-4 animate-fade-in">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <span className="text-3xl">📋</span>
          Final Legal Report
        </h2>
        <button
          onClick={handleDownload}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center gap-2"
        >
          <span>📥</span>
          Download Report
        </button>
      </div>
      <div className="text-gray-700 border-t pt-4">{renderReport()}</div>
    </div>
  );
};

export default FinalReport;

