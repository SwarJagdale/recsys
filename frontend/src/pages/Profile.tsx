import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

interface Interaction {
  product_id: string;
  product_name: string;
  interaction_type: string;
  timestamp: string;
  category: string;
  brand: string;
}

interface ProfileResponse {
  user: {
    email: string;
    name: string;
  };
  recommendation_profile: {
    category_preferences: Record<string, number>;
    brand_preferences: Record<string, number>;
  };
  recent: Interaction[];
  summary: Record<string, number>;
}

const Profile: React.FC = () => {
  const { user } = useAuth();
  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProfile = async () => {
      if (!user) return;
      try {
        const response = await axios.get(`http://localhost:5000/api/profile/${user.user_id}`);
        setProfile(response.data);
      } catch (error) {
        console.error('Error fetching profile:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [user]);

  if (loading) {
    return (
      <div className="container loading-container">
        <div className="spinner"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container">
        <div className="alert alert-error">{error}</div>
      </div>
    );
  }

  return (
    <div className="container">
      <h1>Your Profile</h1>
      
      <div className="grid">
        <div className="card">
          <div className="card-content">
            <h2>Basic Information</h2>
            <p>Email: {profile?.user.email}</p>
          </div>
        </div>

        <div className="card">
          <div className="card-content">
            <h2>Category Preferences</h2>
            {profile?.recommendation_profile.category_preferences && 
              Object.entries(profile.recommendation_profile.category_preferences)
                .map(([category, score]) => (
                  <div key={category} className="preference-item">
                    <div className="preference-header">
                      <span>{category}</span>
                      <span>{(score * 100).toFixed(1)}%</span>
                    </div>
                    <div className="progress-bar">
                      <div 
                        className="progress-fill"
                        style={{ width: `${score * 100}%` }}
                        title={`${(score * 100).toFixed(1)}% preference`}
                      ></div>
                    </div>
                  </div>
                ))
            }
          </div>
        </div>

        <div className="card">
          <div className="card-content">
            <h2>Brand Preferences</h2>
            {profile?.recommendation_profile.brand_preferences && 
              Object.entries(profile.recommendation_profile.brand_preferences)
                .map(([brand, score]) => (
                  <div key={brand} className="preference-item">
                    <div className="preference-header">
                      <span>{brand}</span>
                      <span>{(score * 100).toFixed(1)}%</span>
                    </div>
                    <div className="progress-bar">
                      <div 
                        className="progress-fill"
                        style={{ width: `${score * 100}%` }}
                        title={`${(score * 100).toFixed(1)}% preference`}
                      ></div>
                    </div>
                  </div>
                ))
            }
          </div>
        </div>

        <div className="card">
          <div className="card-content">
            <h2>Recent Activity</h2>
            <div className="activity-list">
              {profile?.recent.map((inter, idx) => (
                <div key={idx} className="activity-item">
                  <h3>{inter.product_name || `Product ${inter.product_id}`}</h3>
                  <p>{`${inter.interaction_type} at ${new Date(inter.timestamp).toLocaleString()}`}</p>
                  <p className="meta">{`${inter.category} - ${inter.brand}`}</p>
                  {idx < (profile.recent.length - 1) && <hr />}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-content">
            <h2>Interaction Summary</h2>
            <table className="summary-table">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Count</th>
                </tr>
              </thead>
              <tbody>
                {profile && Object.entries(profile.summary).map(([type, count]) => (
                  <tr key={type}>
                    <td>{type}</td>
                    <td>{count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;
