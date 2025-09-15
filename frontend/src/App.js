import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import PDFProcessor from './pages/PDFProcessor';
import RAGChat from './pages/RAGChat';
import Text2Cypher from './pages/Text2Cypher';
import AgenticRAG from './pages/AgenticRAG';
import EntityExtraction from './pages/EntityExtraction';
import ContractExtraction from './pages/ContractExtraction';
import GraphRAG from './pages/GraphRAG';
import Statistics from './pages/Statistics';
import KnowledgeGraphConstruction from './pages/KnowledgeGraphConstruction';

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/pdf-processor" element={<PDFProcessor />} />
        <Route path="/rag-chat" element={<RAGChat />} />
        <Route path="/text2cypher" element={<Text2Cypher />} />
        <Route path="/agentic-rag" element={<AgenticRAG />} />
        <Route path="/entity-extraction" element={<EntityExtraction />} />
        <Route path="/contract-extraction" element={<ContractExtraction />} />
        <Route path="/graph-rag" element={<GraphRAG />} />
        <Route path="/statistics" element={<Statistics />} />
        <Route path="/knowledge-graph-construction" element={<KnowledgeGraphConstruction />} />
      </Routes>
    </Layout>
  );
}

export default App;
