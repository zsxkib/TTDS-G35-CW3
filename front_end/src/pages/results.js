import React, { useEffect, useState } from "react"
import { useLocation } from 'react-router-dom';
import { Box } from '@material-ui/core';
import { IconButton, TextField} from '@material-ui/core';
import { SearchOutlined } from '@material-ui/icons';
import logo from '../logo_2.png'
import { useNavigate } from 'react-router-dom';

function SearchBar(){
  const [content, setContent] = useState('');
  let navigate = useNavigate()

  const handleSubmit = (e) => {
    navigate('', { state: { searchTerm: content } });
  };

  return(
    <form className='form_2' onSubmit={handleSubmit}>
          <TextField
              id="search-bar"
              placeholder= "Search"
              value={content}
              onInput={e=>setContent(e.target.value)}
              style={{width:"100%"}}
              InputProps={{
                  endAdornment: (
                      <IconButton type="submit">
                        <SearchOutlined />
                      </IconButton>
                  ),
              }}
              variant="outlined"
          />
      </form>
  )
}

function getDescription(title) {
  if (title != undefined) {
    var des = ""
    fetch("https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exchars=175&titles=" + title.replace(" ", "%20"))
      .then(data => {
        des = data.extract
        console.log(data)
      })
    return des
  }
}

function UsingFetch () {
  const [users, setUsers] = useState([])
  
  let { state } = useLocation();
  let query = state["searchTerm"];

  const fetchData = () => {
    fetch("http://127.0.0.1:8000/search/?query=$".replace("$", query))
      .then(response => {
        return response.json()
      })
      .then(data => {
        setUsers(data["0"])
      })
  }

  useEffect(() => {
    fetchData()
  }, [])
 
  // TODO: WINI PLEASE MAKE THIS LOOK NICE!
  return (
    <div className='resultsPage'>
      <a href={window.location.origin}>
        <img src={logo} alt="Logo" className="logo_2"/>
      </a>
      {SearchBar()}
      <p className = "note">Note: "t:title" searches for pages with title in the title and "b:body" searches for pages with body in the body</p>
      <hr class="dashed"/>
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
                padding= "5px"
              >
                <a href={user.link} className="link">
                  <div className="title" >{user.title}</div>
                </a>
                <div className="description">{getDescription(user.title)}</div>
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