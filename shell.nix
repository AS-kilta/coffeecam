{ pkgs ? import <nixpkgs> {}}:
  pkgs.mkShell {
    nativeBuildInputs = let
      env = pyPkgs : with pyPkgs; [
        python-decouple
        opencv4
      ];
    in with pkgs; [
      (python311.withPackages env)
    ];
}
