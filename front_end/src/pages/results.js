import React, { useEffect, useState } from "react"
import { useLocation } from 'react-router-dom';
import { Box, Grid, TextField, IconButton, FormControl, NativeSelect, InputLabel } from '@material-ui/core';
import { SearchOutlined } from '@material-ui/icons';
import logo from '../logo.png'

function UsingFetch() {
    const [hits, setHits] = useState([]);
    const [content, setContent] = useState('');
    const [hitCounts, setHitCounts] = useState("5");
    const [choice, setChoice] = useState("ranked");
    const [aiAns, setAIAns] = useState("... :)");

    const handleHitCount = (event) => {
        setHitCounts(event.target.value);
    };

    const handleChoice = (event) => {
        setChoice(event.target.value);
    };

    let { state } = useLocation();
    let query = content;
    if (state) {
        query = state["searchTerm"];
    }

    const fetchData = (event) => {
        if (event) {
            setHits([]);
            event.preventDefault();
            query = document.getElementById("search-bar2").value;
        }
        fetch("http://127.0.0.1:8000/search/?query=$".replace("$", query)
            + "&hitcount=$".replace("$", hitCounts)
            + "&choice=$".replace("$", choice))
            .then(response => {
                return response.json()
            })
            .then(data => {
                setHits(data["0"])
            })

        setAIAns("")
        fetch("http://127.0.0.1:8000/search/?query=$".replace("$", query)
            + "&hitcount=$".replace("$", hitCounts)
            + "&choice=$".replace("$", choice)
            + "&question=T" // USE AI
        )
            .then(response => {
                return response.json()
            })
            .then(data => {
                setAIAns(data["0"][0]["description"])
            })
        return false;
    }

    useEffect(() => {
        fetchData();
    }, []);

    return (
        <Grid className='resultsPage' style={{ minHeight: "100vh" }}>
            <a href={window.location.origin}>
                <img src={logo} alt="Logo" className="logo_2" />
            </a>
            <form className='form_2' onSubmit={fetchData} autoComplete="off">
                <TextField
                    id="search-bar2"
                    placeholder="Search"
                    value={content}
                    onInput={e => setContent(e.target.value)}
                    style={{ width: "100%" }}
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
            <div className='dropdown' >
                <div>
                    <FormControl style={{ width: "250px"}}>
                        <InputLabel>Index Choice</InputLabel>
                        <NativeSelect
                            defaultValue={"ranked"}
                            value={choice}
                            onChange={handleChoice}
                        >
                            <option value={"ranked"}>Ranked IR</option>
                            <option value={"rankedbeta"}>BETA Ranked IR</option>
                            <option value={"boolean"}>Boolean Search</option>
                            <option value={"question"}>AI Question Answering</option>
                            <option value={"vector"}>ML Vector Search</option>
                        </NativeSelect>
                    </FormControl>
                </div>
                <div>
                    <FormControl style={{ m: 1, width: "100px" }}>
                        <InputLabel>Hit Counts</InputLabel>
                        <NativeSelect
                            defaultValue={5}
                            value={hitCounts}
                            onChange={handleHitCount}
                        >
                            <option value={5}>5</option>
                            <option value={10}>10</option>
                            <option value={15}>15</option>
                            <option value={20}>20</option>
                        </NativeSelect>
                    </FormControl>
                </div>
            <p className="note">Note: "t:title" searches for pages with "title" in the title and "b:body" searches for pages with "body" in the body</p>
            <hr className="dashed" />
            </div>
            <div className='all-results'>
                {hits.length > 1 && (
                    <div>
                        {(aiAns !== "") && (
                            <div>
                                <Box className="boxes">
                                    <div className="title" ><b><i>Wiki Bot:</i></b></div>
                                    <div className="description"><i>{aiAns}</i></div>
                                </Box>
                                <Box paddingTop="2%"></Box>
                            </div>
                        )}
                        {hits.slice(1).map(hit => (
                            <div>
                                <div className="boxes">
                                    <a href={hit.link} className="link">
                                        <div className="title" >{hit.title}</div>
                                        {(() => {
                                            if (hit.description) {
                                                return <div className="description">{hit.description + "..."}</div>
                                            }
                                        })()}
                                    </a>
                                </div>
                                <Box paddingTop="2%"></Box>
                            </div>
                        ))}
                    </div>
                )}
                {hits.length === 1 && (
                    <div className="title" >No Matches Found :/</div>
                )}
                {hits.length === 0 && (
                    <div className="title" >Loading...</div>
                )}
            </div>
        </Grid>
    )
}

export default UsingFetch;