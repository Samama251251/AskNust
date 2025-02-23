import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Auth from "@/components/auth";
import ChatInterface from "@/components/chatInterface";
import { useEffect, useState } from "react";

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const handleAuthentication = () => {
    console.log("Setting authenticated to true");
    setIsAuthenticated(true);
  };

  useEffect(() => {
    const verifyToken = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          console.log("I am here")
          const response = await fetch('http://localhost:8000/auth/auth', {
            method: 'POST',
            credentials: 'include',
          });
          const data = await response.json();
          setIsAuthenticated(data.isAuthenticated);
        } catch (error) {
          console.error('Authentication error:', error);
          setIsAuthenticated(false);
        }
      }
    };

    verifyToken();
  }, []);

  // Protected Route wrapper component
  const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
    if (!isAuthenticated) {
      return <Navigate to="/login" replace />;
    }
    return <>{children}</>;
  };

  return (
    <BrowserRouter>
      <Routes>
        {/* Public route */}
        <Route 
          path="/login" 
          element={isAuthenticated ? 
            <Navigate to="/chat" replace /> : 
            <Auth onAuthentication={handleAuthentication} />
          } 
        />

        {/* Protected route */}
        <Route
          path="/chat"
          element={
            <ProtectedRoute>
              <ChatInterface/>
            </ProtectedRoute>
          }
        />

        {/* Default route - redirects based on auth status */}
        <Route
          path="/"
          element={
            isAuthenticated ? <Navigate to="/chat" replace /> : <Navigate to="/login" replace />
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
