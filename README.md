## How to Run the App

Follow these steps to set up and run the app:

1. **Set Up the API Key**:
   - Obtain an API key from OpenAI.
   - Navigate to the `backend` directory.
   - Create a `.env` file and add the following line, replacing `your_openai_api_key_here` with your actual API key:
     ```env
     OPENAI_API_KEY="your_openai_api_key_here"
     ```

2. **Start the Backend**:
   - Open a terminal in the root directory of the project.
   - Run the following command to start the backend:
     ```bash
     python3 backend/backend.py
     ```

3. **Start the Frontend**:
   - Open another terminal in the root directory.
   - Run the following command to start the frontend:
     ```bash
     npm start
     ```

4. **Access the App**:
   - Open your browser and navigate to [http://localhost:3000](http://localhost:3000).

5. **Use the App**:
   - Once the app is running, provide a `.pdf` link for analysis. For example:
     [https://arxiv.org/pdf/2412.10265.pdf](https://arxiv.org/pdf/2412.10265.pdf)