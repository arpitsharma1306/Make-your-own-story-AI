import {useState, useEffect} from "react"
import {useNavigate} from "react-router-dom";
import axios from "axios";
import ThemeInput from "./ThemeInput.jsx";
import LoadingStatus from "./LoadingStatus.jsx";
import {API_BASE_URL} from "../util.js";


function StoryGenerator() {
    const navigate = useNavigate()
    const [theme, setTheme] = useState("")
    const [jobId, setJobId] = useState(null)
    const [jobStatus, setJobStatus] = useState(null)
    const [error, setError] = useState(null)
    const [loading, setLoading] = useState(false)

    useEffect(() => {
        let pollInterval;

        if (jobId && jobStatus === "processing") {
            pollInterval = setInterval(() => {
                pollJobStatus(jobId)
            }, 5000)
        }

        return () => {
            if (pollInterval) {
                clearInterval(pollInterval)
            }
        }
    }, [jobId, jobStatus])

    const generateStory = async (theme) => {
        setLoading(true)
        setError(null)
        setTheme(theme)

        try {
            console.log(`Sending request to ${API_BASE_URL}/stories/create with theme: ${theme}`)
            const response = await axios.post(`${API_BASE_URL}/stories/create`, {theme})
            console.log('Response received:', response.data)
            const {job_id, status} = response.data
            setJobId(job_id)
            setJobStatus(status)

            pollJobStatus(job_id)
        } catch (e) {
            console.error('Error generating story:', e)
            setLoading(false)
            let errorMessage = `Failed to generate story: ${e.message}`
            
            // Add more detailed error information if available
            if (e.response) {
                // The request was made and the server responded with a status code
                // that falls out of the range of 2xx
                errorMessage += ` (Status: ${e.response.status})`
                if (e.response.data && e.response.data.detail) {
                    errorMessage += ` - ${e.response.data.detail}`
                }
                console.error('Error response:', e.response.data)
            } else if (e.request) {
                // The request was made but no response was received
                errorMessage = 'Network error: No response received from server. Please check your internet connection.'
                console.error('No response received:', e.request)
            }
            
            setError(errorMessage)
        }
    }

    const pollJobStatus = async (id) => {
        try {
            console.log(`Polling job status for job ID: ${id}`)
            const response = await axios.get(`${API_BASE_URL}/jobs/${id}`)
            console.log('Job status response:', response.data)
            const {status, story_id, error: jobError} = response.data
            setJobStatus(status)

            if (status === "completed" && story_id) {
                console.log(`Job completed successfully with story ID: ${story_id}`)
                fetchStory(story_id)
            } else if (status === "failed" || jobError) {
                console.error(`Job failed with error: ${jobError}`)
                setError(jobError || "Failed to generate story")
                setLoading(false)
            } else {
                console.log(`Job status: ${status}, continuing to poll...`)
            }
        } catch (e) {
            console.error('Error polling job status:', e)
            if (e.response?.status !== 404) {
                let errorMessage = `Failed to check story status: ${e.message}`
                
                // Add more detailed error information if available
                if (e.response) {
                    errorMessage += ` (Status: ${e.response.status})`
                    if (e.response.data && e.response.data.detail) {
                        errorMessage += ` - ${e.response.data.detail}`
                    }
                    console.error('Error response:', e.response.data)
                } else if (e.request) {
                    errorMessage = 'Network error: No response received from server while checking story status.'
                    console.error('No response received:', e.request)
                }
                
                setError(errorMessage)
                setLoading(false)
            }
        }
    }

    const fetchStory = async (id) => {
        try {
            console.log(`Fetching story with ID: ${id}`)
            setLoading(false)
            setJobStatus("completed")
            navigate(`/story/${id}`)
        } catch (e) {
            console.error('Error fetching story:', e)
            let errorMessage = `Failed to load story: ${e.message}`
            
            // Add more detailed error information if available
            if (e.response) {
                errorMessage += ` (Status: ${e.response.status})`
                if (e.response.data && e.response.data.detail) {
                    errorMessage += ` - ${e.response.data.detail}`
                }
                console.error('Error response:', e.response.data)
            } else if (e.request) {
                errorMessage = 'Network error: No response received from server while loading story.'
                console.error('No response received:', e.request)
            }
            
            setError(errorMessage)
            setLoading(false)
        }
    }

    const reset = () => {
        setJobId(null)
        setJobStatus(null)
        setError(null)
        setTheme("")
        setLoading(false)
    }

    return <div className="story-generator">
        {error && <div className="error-message">
            <p>{error}</p>
            <button onClick={reset}>Try Again</button>
        </div>}

        {!jobId && !error && !loading && <ThemeInput onSubmit={generateStory}/>}

        {loading && <LoadingStatus theme={theme} />}
    </div>
}

export default StoryGenerator