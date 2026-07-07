import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import SultanConsole from "@/pages/SultanConsole";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<SultanConsole />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
