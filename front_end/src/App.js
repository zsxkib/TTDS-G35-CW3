import './App.css';
import { Routes, Route } from "react-router-dom";
import SearchBar from './pages/search';
import Result from './pages/results'

const App = () => {
  return (
    <Routes>
      <Route path="/" element={<SearchBar />}></Route>
      <Route path="/result" element={<Result />}></Route>
    </Routes>

  );
}

export default App;
