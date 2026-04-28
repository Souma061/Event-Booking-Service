import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/useAuth";

export default function OAuthCallback() {
    const navigate = useNavigate();
    const { login } = useAuth();

    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        const token = params.get("token");

        const completeLogin = async () => {
            if (!token) {
                console.error("OAuth callback did not contain a token.");
                navigate("/login?error=invalid_token");
                return;
            }

            try {
                await login(token);
                navigate("/");
            } catch (err) {
                console.error("OAuth login failed.", err);
                navigate("/login?error=oauth_failed");
            }
        };

        completeLogin();
    }, [login, navigate]);

    return (
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100vh" }}>
            <h2>Processing OAuth Callback...</h2>
        </div>
    );
}
