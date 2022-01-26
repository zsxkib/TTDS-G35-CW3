import { IconButton, TextField} from '@material-ui/core';
import { SearchOutlined } from '@material-ui/icons';
import React, { useState } from "react";

const SearchBar = (props) => {
    const [content, setContent] = useState('');
    const handleSubmit = (e) => {
        alert(content);
        e.preventdefault()
    };

  return (
        <form className='form' onSubmit={handleSubmit}>
            <TextField
                id="search-bar"
                placeholder= "How can we help?"
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
  );
}

export default SearchBar;