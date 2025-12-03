const PartialReportCard = ({ report }) => {
  return (
    <div className="mb-4 p-4 bg-white border border-gray-300 rounded-lg shadow-sm">
      <h3 className="text-lg font-semibold mb-2 text-gray-800">
        Current Analysis
      </h3>
      <p className="text-gray-600 text-sm whitespace-pre-wrap">
        {report || 'Gathering information...'}
      </p>
    </div>
  );
};

export default PartialReportCard;

