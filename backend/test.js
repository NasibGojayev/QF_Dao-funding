async function signupUser() {
  try {
    const response = await fetch("http://127.0.0.1:8000/signup/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: "Nasib",
        email: "nasib@example.com",
        password: "123456"
      }),
    });

    // Check if response is JSON
    const text = await response.text();
    try {
      const data = JSON.parse(text);
      console.log("JSON response:", data);
    } catch {
      console.log("Non-JSON response:", text);
    }
  } catch (err) {
    console.error("Fetch failed:", err);
  }
}

signupUser();
