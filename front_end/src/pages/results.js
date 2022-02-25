import { IconButton, TextField} from '@material-ui/core';
import { SearchOutlined } from '@material-ui/icons';
import React, { useState } from "react";
import logo from '../logo_2.png'
import icon from '../icon.png'
import { Box } from '@material-ui/core';
import { useNavigate } from 'react-router-dom';
import { dummyData } from "../data";

function ResultsPage () {
  let navigate = useNavigate()
  const [content, setContent] = useState('');

  // TODO: CHANGE POST TO GET AND OVERWRITE DUMMYDATA IN results.js
  const handleSubmit = (e) => {
      const requestOptions = {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            searchTerm: content,
          })
        };
      fetch("http://127.0.0.1:8000/search/", requestOptions)
      navigate('./result')
  };
  const searchForTerm = (e) => {
    const requestOptions = {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          searchTerm: content,
        })
      };
    fetch("http://127.0.0.1:8000/search/", requestOptions)
    navigate('./result')
};
  
  //const classes = useStyles();

  return (
    <div className='resultsPage'>
      <div className="sidebar">
        <img src={icon} alt="Icon" className="icon"/>
      </div>
      <div className='main_results'>
        <img src={logo} alt="Logo" className="logo_2"/>
        <form className='form_2' onSubmit={handleSubmit}>
            <TextField
                id="search-bar"
                placeholder= "Search"
                value={content}
                onInput={ e=>setContent(e.target.value)}
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
        <hr class="dashed"/>
        <div className='all-results'>
          {dummyData.map((data) => {
              return (
                <div>
                  <Box 
                    border={2}
                    borderRadius="6px"
                    alignContent="center"
                    width="60%"
                    borderColor="#9FBBA5"
                    color="#362706"
                    padding= "5px"
                  >
                    <div className="title">
                      {data.title}
                    </div>
                    <div className="description">
                      {data.description}
                    </div>
                  </Box>
                  <Box paddingTop="2%"></Box>
                </div>
              );
            })}
        </div>
      </div>
    </div>
  );
}

export default ResultsPage;