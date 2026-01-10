import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ConfigProvider } from "antd";
import zhCN from "antd/locale/zh_CN";
import HomePage from "./pages/HomePage";
import DatabasePage from "./pages/DatabasePage";
import "./styles/globals.css";

const App: React.FC = () => {
  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/database/:name" element={<DatabasePage />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
};

export default App;
