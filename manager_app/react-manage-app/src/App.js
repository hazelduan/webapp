import React, { useState, useEffect } from 'react';
import logo from './logo.svg';
import './App.css';

function App() {
  // usestate for setting a javascript
    // object for storing and using data
    const [data, setdata] = useState({
      name: "",
      date: "",
      programming: "",
  });

  useEffect(() => {
    fetch('/api/time').then(res => 
      res.json()).then(data => {
        // Setting a data from api
        setdata({
          name: data.Name,
          date: data.Date,
          programming: data.programming,
        });
      });
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <a
          className="App-link"
          href="https://reactjs.org"
          target="_blank"
          rel="noopener noreferrer"
        >
          Learn React
        </a>
      
        <h1>React and flask</h1>
        {/* Calling a data from setdata for showing */}
        <p>{data.name}</p>
        <p>{data.date}</p>
        <p>{data.programming}</p>
  
      </header>
    </div>
  );
}

export default App;
