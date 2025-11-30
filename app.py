import express from 'express';
import cors from 'cors';
import axios from 'axios';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
const port = process.env.PORT || 5000;

const allowedOrigins = [
	'https://instagram-video-downloader-delta.vercel.app',
	'http://127.0.0.1:5500',
	'http://localhost:5500', 
];

app.use(
	cors({
		origin: (origin, callback) => {
			if (!origin || allowedOrigins.includes(origin)) {
				callback(null, true);
			} else {
				callback(new Error('Not allowed by CORS'));
			}
		},
		credentials: true, 
	}),
);
app.use(express.json());
app.get("/test", (req, res) => {
		res.status(200).json({ success: success, message: 'hello' });
})

app.get('/download', async (req, res) => {
	console.log('hello');

	const { url } = req.query; 
	console.log('URL:', url);

	// Validate URL
	if (!url || !url.startsWith('https://www.instagram.com')) {
		return res.status(400).json({ success: false, message: 'A valid Instagram URL is required.' });
	}

	try {
		const options = {
			method: 'GET',
			url: 'https://instagram-reels-downloader-api.p.rapidapi.com/download',
			params: {
				url: url,
				userId: '25025320',
			},

			headers: {
				'x-rapidapi-key': '12c2fa05b3mshccf8a4b3eb452ccp1380b7jsn71e1f5190176' || process.env.RAPIDAPI_KEY,
				'x-rapidapi-host': 'instagram-reels-downloader-api.p.rapidapi.com',
			},
		};

		// Make the request to RapidAPI
		const response = await axios(options);
		console.log(response);

		// Debugging: Log the full response
		console.log('API Response:', JSON.stringify(response.data, null, 2));

		// Extract the video URL from the medias array
		if (!response.data.data.medias || response.data.data.medias.length === 0) {
			return res.status(404).json({ success: false, message: 'No video found in the response.' });
		}

		const videoUrl = response.data.data.medias[0].url;

		// Send the video URL back to the client
		res.json({ success: true, videoUrl: videoUrl });
	} catch (error) {
		console.error('Error:', error.response ? error.response.data : error.message);
		console.log(error);
		res.status(500).json({ success: false, message: 'Failed to fetch reels.', error });
	}
});

export default app;
