import { useState } from "react"
import Login from "./login"
import Signup from "./signup"
import { Toaster } from 'react-hot-toast'

interface AuthProps {
  onAuthentication: () => void;
}

const Auth = ({ onAuthentication }: AuthProps) => {
  const [activeTab, setActiveTab] = useState("login")

  const handleLoginSuccess = (token: string) => {
    // Save token to localStorage
    localStorage.setItem('token', token)
    console.log("Token saved, updating authentication state")
    // Update the authentication state in App.tsx
    onAuthentication()
    // The navigation will now happen automatically due to the route configuration
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200 py-12 px-4 sm:px-6 lg:px-8">
      <Toaster position="top-center" />
      <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-2xl shadow-2xl">
        <div>
          <h2 className="mt-6 text-center text-4xl font-extrabold text-gray-900">Welcome to AskNust</h2>
          <p className="mt-2 text-center text-sm text-gray-600">Your AI-powered conversation companion</p>
        </div>
        <div className="mt-8">
          <div className="flex justify-center mb-6">
            <div className="inline-flex rounded-full p-1 bg-gray-100">
              <button
                onClick={() => setActiveTab("login")}
                className={`px-6 py-2 text-sm font-medium rounded-full transition-all duration-300 ${
                  activeTab === "login" ? "bg-black text-white shadow-md" : "text-gray-500 hover:text-gray-900"
                }`}
              >
                Login
              </button>
              <button
                onClick={() => setActiveTab("signup")}
                className={`px-6 py-2 text-sm font-medium rounded-full transition-all duration-300 ${
                  activeTab === "signup" ? "bg-black text-white shadow-md" : "text-gray-500 hover:text-gray-900"
                }`}
              >
                Sign Up
              </button>
            </div>
          </div>
          {activeTab === "login" ? <Login onLoginSuccess={handleLoginSuccess} /> : <Signup onLoginSuccess={handleLoginSuccess} />}
        </div>
      </div>
    </div>
  )
}

export default Auth

