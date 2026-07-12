package cl.benjamin.claveunica.dto;

import jakarta.validation.constraints.NotBlank;

public record ActionRequest(
  @NotBlank String screenRoute,
  @NotBlank String action
) {}
