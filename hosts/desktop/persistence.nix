{ username, ... }:

{
  environment.persistence."/persist" = {
    hideMounts = true;

    files = [ "/etc/machine-id" ];

    directories = [
      {
        directory = "/etc/nixos";
        user = username;
        group = "users";
        mode = "0755";
      }

      {
        directory = "/etc/NetworkManager/system-connections";
        mode = "0700";
      }
    ];
  };
}
