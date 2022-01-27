import { IconButton, TextField} from '@material-ui/core';
import { SearchOutlined } from '@material-ui/icons';
import React, { useState } from "react";

const SearchBar = (props) => {
    const [content, setContent] = useState('');
    const { spawn } = require('child_process');
    const handleSubmit = (e) => {
        var dataToSend;
        const python = spawn('python3', ['../python/_search.py']);
        alert(python)

        python.stdout.on('data', function(data) {
            dataToSend = data.toString();
        });

        python.stderr.on('data', data => {
            console.error(`stderr: ${data}`);
        });

        python.on('exit', (code) => {
            console.log(`child process exited with code ${code}, ${dataToSend}`);
        })
        
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