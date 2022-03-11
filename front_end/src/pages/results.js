import React, { useEffect, useState } from "react"
import { useLocation } from 'react-router-dom';
import { Box } from '@material-ui/core';
import { IconButton, TextField } from '@material-ui/core';
import { SearchOutlined } from '@material-ui/icons';
import logo from '../logo_2.png'

function UsingFetch() {
  const [users, setUsers] = useState([])
  const [content, setContent] = useState('');

  let { state } = useLocation();
  let query = content;
  if (state) {
    query = state["searchTerm"];
  }

  const fetchData = (event) => {
    if (event) {
      event.preventDefault();
      query = event.currentTarget[0].defaultValue
    }
    fetch("http://127.0.0.1:8000/search/?query=$".replace("$", query))
      .then(response => {
        return response.json()
      })
      .then(data => {
        setUsers(data["0"])
      })


    return false;
  }

  useEffect(() => {
    fetchData()
  }, [])

  return (
    <div className='resultsPage'>
      <a href={window.location.origin}>
        <img src={logo} alt="Logo" className="logo_2" />
      </a>
      <form className='form_2' onSubmit={fetchData}>
        <TextField
          id="search-bar2"
          placeholder="Search"
          value={content}
          onInput={e => setContent(e.target.value)}
          style={{ width: "100%" }}
          variant="outlined"
        />
      </form>
      <p className="note">Note: "t:title" searches for pages with title in the title and "b:body" searches for pages with body in the body</p>
      <hr class="dashed" />
      {users.length > 0 && (
        <div className='all-results'>
          {users.map(user => (
            <div>
              <Box
                className="boxes"
                border={2}
                borderRadius="6px"
                alignContent="center"
                width="90%"
                borderColor="#9FBBA5"
                color="#362706"
                padding="5px"
              >
                <a href={user.link} className="link">
                  <div className="title" >{user.title}</div>
                </a>
                {/* <div className="description">users.map(user]{getDescription(user.title)}</div> */}
              </Box>
              <Box paddingTop="2%"></Box>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default UsingFetch;