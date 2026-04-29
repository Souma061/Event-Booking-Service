import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/useAuth";

export default function OAuthCallback() {
    const navigate = useNavigate();
    const { fetchUser } = useAuth();
    const didRun = useRef(false);

    useEffect(() => {
        // Prevent double-execution in React StrictMode
        if (didRun.current) return;
        didRun.current = true;

        const completeLogin = async () => {
            try {
                // The backend already set the HTTP-only cookie on the redirect.
                // We just need to fetch the current user to hydrate the auth state.
                await fetchUser();
                navigate("/");
            } catch (err) {
                console.error("OAuth login failed — could not verify session.", err);
                navigate("/login?error=oauth_failed");
            }
        };

        completeLogin();
    }, [fetchUser, navigate]);

    return (
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100vh" }}>
            <h2>Processing OAuth Callback...</h2>
        </div>
    );
}
