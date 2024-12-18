## How to run the app

First, ensure that you have obtained an API key from OpenAI. 

Then, create a `.env` file in your `backend` directory and add the following line:

     ```plaintext
     OPENAI_API_KEY="your_openai_api_key_here"
     ```

In the root directory, you can run:

### `python3 backend/backend.py`

Then in another terminal, also in the root directory, run:

### `npm start`

Then open [http://localhost:3000](http://localhost:3000) to view the app in your browser.

Once the app is running, provide a link for analysis that ends in .pdf. For example:

[https://arxiv.org/pdf/2412.10265.pdf](https://arxiv.org/pdf/2412.10265.pdf)