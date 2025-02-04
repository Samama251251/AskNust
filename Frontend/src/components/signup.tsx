import React, { useState } from "react";
import { toast } from "react-hot-toast";
import { PulseLoader } from 'react-spinners';

interface SignupProps {
  onLoginSuccess: (token: string) => void;
}

const Signup = ({ onLoginSuccess }: SignupProps) => {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setPasswordError("Passwords do not match");
      toast.error("Passwords do not match. Please try again.", {
        duration: 3000,
      });
      return;
    }
    
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password, name }),
        credentials: 'include',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Signup failed');
      }

      const data = await response.json();
      toast.success('Signup successful!');
      onLoginSuccess(data.access_token);

    } catch (error) {
      console.error('Signup error:', error);
      toast.error(error instanceof Error ? error.message : 'Signup failed');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px]">
        <PulseLoader color="#000000" size={15} margin={2} />
        <p className="mt-4 text-gray-600">Creating your account...</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label
          htmlFor="name"
          className="block text-sm font-medium text-gray-700"
        >
          Name
        </label>
        <input
          type="text"
          id="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          className="mt-1 block w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-full shadow-sm focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent transition-all duration-300"
        />
      </div>
      <div>
        <label
          htmlFor="email"
          className="block text-sm font-medium text-gray-700"
        >
          Email
        </label>
        <input
          type="email"
          id="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          onInvalid={(e) => {
            e.preventDefault();
            toast.error("Please enter a valid email address");
          }}
          required
          className="mt-1 block w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-full shadow-sm focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent transition-all duration-300"
        />
      </div>
      <div>
        <label
          htmlFor="password"
          className="block text-sm font-medium text-gray-700"
        >
          Password
        </label>
        <input
          type="password"
          id="password"
          value={password}
          onChange={(e) => {
            setPassword(e.target.value);
            setPasswordError("");
          }}
          required
          className="mt-1 block w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-full shadow-sm focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent transition-all duration-300"
        />
      </div>
      <div>
        <label
          htmlFor="confirmPassword"
          className="block text-sm font-medium text-gray-700"
        >
          Confirm Password
        </label>
        <input
          type="password"
          id="confirmPassword"
          value={confirmPassword}
          onChange={(e) => {
            setConfirmPassword(e.target.value);
            setPasswordError("");
          }}
          required
          className="mt-1 block w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-full shadow-sm focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent transition-all duration-300"
        />
        {passwordError && (
          <p className="mt-2 text-sm text-red-600">{passwordError}</p>
        )}
      </div>
      <div>
        <button
          type="submit"
          disabled={isLoading}
          className="w-full flex justify-center py-3 px-4 border border-transparent rounded-full shadow-sm text-sm font-medium text-white bg-black hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-black transition-all duration-300 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          ) : (
            'Sign Up'
          )}
        </button>
      </div>
      <div className="text-sm text-center">
        <p className="text-gray-600">
          By signing up, you agree to our{" "}
          <a href="#" className="font-medium text-black hover:text-gray-800">
            Terms
          </a>{" "}
          and{" "}
          <a href="#" className="font-medium text-black hover:text-gray-800">
            Privacy Policy
          </a>
        </p>
      </div>
    </form>
  );
};

export default Signup;
