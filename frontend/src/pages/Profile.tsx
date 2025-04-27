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
  Alert
} from '@mui/material';

interface Interaction {
  product_id: string;
  interaction_type: string;
  timestamp: string;
}

interface ProfileResponse {
  user: {
    email: string;
    preferences: any;
  };
  summary: Record<string, number>;
  recent: Interaction[];
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
      <Typography variant="h6">Email: {profile?.user.email}</Typography>

      <Typography variant="h6" sx={{ mt: 2 }}>
        Preferences:
      </Typography>
      <Box component="pre" sx={{ bgcolor: '#f0f0f0', p: 2, borderRadius: 1 }}>
        {JSON.stringify(profile?.user.preferences, null, 2)}
      </Box>

      <Typography variant="h6" sx={{ mt: 2 }}>
        Interaction Summary:
      </Typography>
      <Table sx={{ maxWidth: 400, bgcolor: '#fafafa' }}>
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

      <Typography variant="h6" sx={{ mt: 2 }}>
        Recent Interactions:
      </Typography>
      <List>
        {profile?.recent.map((inter, idx) => (
          <React.Fragment key={idx}>
            <ListItem>
              <ListItemText
                primary={`Product ${inter.product_id}`}
                secondary={`${inter.interaction_type} at ${new Date(inter.timestamp).toLocaleString()}`}
              />
            </ListItem>
            {idx < (profile.recent.length - 1) && <Divider component="li" />}
          </React.Fragment>
        ))}
      </List>
    </Box>
  );
};

export default Profile;
