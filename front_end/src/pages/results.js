import { IconButton, TextField} from '@material-ui/core';
import { SearchOutlined } from '@material-ui/icons';
import React, { useState } from "react";
import logo from '../logo_2.png'
import icon from '../icon.png'
import { Box } from '@material-ui/core';
import { useNavigate } from 'react-router-dom';
import { dummyData } from "../data";
import {useLocation} from 'react-router-dom';

import Async from 'react-async';

const loadUsers = (query) =>
  fetch("http://127.0.0.1:8000/search/?query=$".replace("$", query))
    .then(res => (res.ok ? res : Promise.reject(res)))
    .then(res => res.json());

// Our component
function ResultsPage() {
  const { state } = useLocation();
  var query = state["searchTerm"];
  return (
    <div className="container">
      <Async promiseFn={loadUsers(query)}>
        {({ data, err, isLoading }) => {
          if (isLoading) return "Loading..."
          if (err) return `Something went wrong: ${err.message}`

          if (data)
            console.log(data)
            return (
              <div>
                <div>
                  <h2>React Async - Random Users</h2>
                </div>
                {data["0"].map(user=> (
                  <div key={user.title} className="row">
                    <div className="col-md-12">
                      <p>{user.link}</p>
                      <p>{user.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            )
        }}
      </Async>
    </div>
  );
}

export default ResultsPage;

// DATA IS THIS!
// #   "0": [
// #     {
//   #       "title": "69171296",
//   #       "link": "https://en.wikipedia.org/?curid=69171296",
//   #       "description": "69171296"
//   #     },
//   #     {
//   #       "title": "69171296",
//   #       "link": "https://en.wikipedia.org/?curid=69171296",
//   #       "description": "69171296"
//   #     }
//   #   ]
//   # }