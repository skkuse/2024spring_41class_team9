import { ReactNode, useState } from "react";

import { Container } from "@mui/material";

// import TopBar, { TOP_BAR_HEIGHT } from "@/lib/components/TopBar";
// import ProfileContext from "@/lib/contexts/ProfileContext";
// import { FullProfileFragment } from "@/lib/gql/graphql";

type Props = {
  children?: ReactNode;
};

function AppLayout({ children }: Props) {
  // const [profileState, setProfile] = useState(profile);
  return (
    <Container maxWidth={false} disableGutters>
      {/* <TopBar profile={profileState} /> */}
      <Container
        maxWidth={false}
        // sx={{ marginTop: `${TOP_BAR_HEIGHT}px` }}
        disableGutters
      >
        {children}
      </Container>
    </Container>
  );
}

export default AppLayout;
