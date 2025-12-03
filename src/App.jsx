import { Toaster } from 'react-hot-toast';
import Home from './pages/Home';

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Toaster position="bottom-right" />
      <Home />
    </div>
  );
}

export default App;

