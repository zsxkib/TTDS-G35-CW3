import React, { useEffect, useState } from "react"
import { useLocation } from 'react-router-dom';
import { Box } from '@material-ui/core';
import { TextField } from '@material-ui/core';
import logo from '../logo_2.png'

function UsingFetch() {
    const [hits, setHits] = useState([])
    const [content, setContent] = useState('');

    let { state } = useLocation();
    let query = content;
    if (state) {
        query = state["searchTerm"];
    }

    const fetchData = (event) => {
        if (event) {
            setHits([])
            event.preventDefault();
            query = event.currentTarget[0].defaultValue
        }
        fetch("http://127.0.0.1:8000/search/?query=$".replace("$", query))
            .then(response => {
                return response.json()
            })
            .then(data => {
                setHits(data["0"])
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
            <form className='form_2' onSubmit={fetchData} autoComplete="off">
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
            {hits.length > 1 && (
                <div className='ans-results'>
                    {hits.slice(0, 1).map(hit => (
                        <div>
                            <Box
                                className="boxes"
                                border={2}
                                margin="auto"
                                borderRadius="6px"
                                alignContent="center"
                                width="50%"
                                borderColor="#9FBBA5"
                                textAlign="center"
                                color="#362706"
                                padding="5px"
                            >
                                <div className="title" >Wiki Bot:</div>
                                <div className="description"><i>{hit.description + "... :)"}</i></div>
                            </Box>
                            <Box paddingTop="2%"></Box>
                        </div>
                    ))}
                    {hits.slice(1).map(hit => (
                        <div>
                            <Box
                                className="boxes"
                                border={2}
                                margin="auto"
                                borderRadius="6px"
                                alignContent="center"
                                width="50%"
                                borderColor="#9FBBA5"
                                color="#362706"
                                padding="5px"
                            >
                                <a href={hit.link} className="link">
                                    <div className="title" >{hit.title}</div>
                                    <div className="description">{hit.description}</div>
                                </a>
                            </Box>
                            <Box paddingTop="2%"></Box>
                        </div>
                    ))}
                </div>
            )}
            {hits.length == 1 && (
                <div className='all-results'>
                    <Box
                        className="boxes"
                        border={2}
                        margin="auto"
                        borderRadius="6px"
                        alignContent="center"
                        width="50%"
                        borderColor="#9FBBA5"
                        color="#362706"
                        padding="5px"
                    >
                        <div className="title" >No Matches Found :/</div>
                    </Box>
                    <Box paddingTop="2%"></Box>
                </div>
            )}
            {hits.length == 0 && (
                <div className='all-results'>
                    <Box
                        className="boxes"
                        border={2}
                        margin="auto"
                        borderRadius="6px"
                        alignContent="center"
                        width="50%"
                        borderColor="#9FBBA5"
                        color="#362706"
                        padding="5px"
                    >
                        <div className="title" >Loading...</div>
                    </Box>
                    <Box paddingTop="2%"></Box>
                </div>
            )}
        </div>
    )
}

export default UsingFetch;