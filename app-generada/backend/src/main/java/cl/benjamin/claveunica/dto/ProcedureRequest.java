package cl.benjamin.claveunica.dto;

import jakarta.validation.constraints.NotBlank;

public record ProcedureRequest(@NotBlank String name) {}
