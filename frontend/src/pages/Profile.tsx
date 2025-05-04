import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { 
  Box,
  Typography,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  List,
  ListItem,
  ListItemText,
  Divider,
  CircularProgress,
  Alert,
  Paper,
  Grid,
  LinearProgress,
  Tooltip
} from '@mui/material';

interface Interaction {
  product_id: string;
  interaction_type: string;
  timestamp: string;
  product_name?: string;
  category?: string;
  brand?: string;
}

interface ProfileResponse {
  user: {
    email: string;
    preferences: any;
  };
  summary: Record<string, number>;
  recent: Interaction[];
  recommendation_profile: {
    category_preferences: Record<string, number>;
    brand_preferences: Record<string, number>;
    interaction_patterns: Record<string, number>;
  };
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
        const res = await axios.get<ProfileResponse>(
          `http://localhost:5000/api/profile/${user.userId}`
        );
        setProfile(res.data);
      } catch (err: any) {
        setError(err.message || 'Error loading profile.');
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, [user]);

  if (loading) {
    return (
      <Box p={3} display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        Your Profile
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6">Basic Information</Typography>
            <Typography>Email: {profile?.user.email}</Typography>
          </Paper>
        </Grid>

        {/* Recommendation Profile */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Category Preferences</Typography>
            {profile?.recommendation_profile.category_preferences && 
              Object.entries(profile.recommendation_profile.category_preferences)
                .map(([category, score]) => (
                  <Box key={category} sx={{ my: 1 }}>
                    <Typography variant="body2" sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>{category}</span>
                      <span>{(score * 100).toFixed(1)}%</span>
                    </Typography>
                    <Tooltip title={`${(score * 100).toFixed(1)}% preference`}>
                      <LinearProgress 
                        variant="determinate" 
                        value={score * 100} 
                        sx={{ height: 8, borderRadius: 4 }}
                      />
                    </Tooltip>
                  </Box>
                ))
            }
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Brand Preferences</Typography>
            {profile?.recommendation_profile.brand_preferences && 
              Object.entries(profile.recommendation_profile.brand_preferences)
                .map(([brand, score]) => (
                  <Box key={brand} sx={{ my: 1 }}>
                    <Typography variant="body2" sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>{brand}</span>
                      <span>{(score * 100).toFixed(1)}%</span>
                    </Typography>
                    <Tooltip title={`${(score * 100).toFixed(1)}% preference`}>
                      <LinearProgress 
                        variant="determinate" 
                        value={score * 100} 
                        sx={{ height: 8, borderRadius: 4 }}
                        color="secondary"
                      />
                    </Tooltip>
                  </Box>
                ))
            }
          </Paper>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Recent Activity</Typography>
            <List>
              {profile?.recent.map((inter, idx) => (
                <React.Fragment key={idx}>
                  <ListItem>
                    <ListItemText
                      primary={inter.product_name || `Product ${inter.product_id}`}
                      secondary={
                        <>
                          {`${inter.interaction_type} at ${new Date(inter.timestamp).toLocaleString()}`}
                          <br />
                          {`${inter.category} - ${inter.brand}`}
                        </>
                      }
                    />
                  </ListItem>
                  {idx < (profile.recent.length - 1) && <Divider component="li" />}
                </React.Fragment>
              ))}
            </List>
          </Paper>
        </Grid>

        {/* Interaction Summary */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Interaction Summary</Typography>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Type</TableCell>
                  <TableCell>Count</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {profile && Object.entries(profile.summary).map(([type, count]) => (
                  <TableRow key={type}>
                    <TableCell>{type}</TableCell>
                    <TableCell>{count}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Profile;
