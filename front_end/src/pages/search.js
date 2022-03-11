import { IconButton, TextField} from '@material-ui/core';
import { SearchOutlined } from '@material-ui/icons';
import React, { useState } from "react";
import { Grid } from '@material-ui/core';
import logo from '../logo.png'
import { useNavigate } from 'react-router-dom';

function SearchPage () {
  let navigate = useNavigate()
  const [content, setContent] = useState('');

  const handleSubmit = (e) => {
    navigate('./result', { state: { searchTerm: content } });
};
  
  return (
    <Grid 
        container 
        justify="center" 
        alignItems="center"
        direction="column"
        className='searchPage'
        style={{minHeight:"100vh"}}>
          <div style={{textAlign:"center"}}>
            <a href={window.location.origin}>
              <img src={logo} alt="Logo" className="logo"/>
            </a>
          </div>
          <form className='form' onSubmit={handleSubmit}>
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
    </Grid>
  );
}

export default SearchPage;