import * as React from "react";
import { Check, ChevronsUpDown, Plus } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

interface LawyerComboboxProps {
  value: string;
  onChange: (value: string) => void;
  options: string[];
  className?: string;
  placeholder?: string;
}

export function LawyerCombobox({
  value,
  onChange,
  options,
  className,
  placeholder = "Sin asignar",
}: LawyerComboboxProps) {
  const [open, setOpen] = React.useState(false);
  const [searchValue, setSearchValue] = React.useState("");

  const handleSelect = (currentValue: string) => {
    onChange(currentValue);
    setOpen(false);
    setSearchValue("");
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className={cn("justify-between px-2 font-normal text-xs h-8", className)}
        >
          <span className="truncate">
            {value && value !== "sin_asignar" ? value : placeholder}
          </span>
          <ChevronsUpDown className="ml-2 h-3 w-3 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[250px] p-0" align="start">
        <Command>
          <CommandInput
            placeholder="Buscar o crear abogado..."
            value={searchValue}
            onValueChange={setSearchValue}
          />
          <CommandList>
            <CommandEmpty>
              <div className="flex flex-col items-center gap-2 p-4 text-sm text-center">
                <span className="text-muted-foreground">No encontrado.</span>
                {searchValue && (
                  <Button
                    size="sm"
                    variant="secondary"
                    className="w-full"
                    onClick={() => handleSelect(searchValue)}
                  >
                    <Plus className="mr-2 h-4 w-4" />
                    Crear "{searchValue}"
                  </Button>
                )}
              </div>
            </CommandEmpty>
            <CommandGroup>
              <CommandItem value="sin_asignar" onSelect={() => handleSelect("sin_asignar")}>
                <Check
                  className={cn(
                    "mr-2 h-4 w-4",
                    value === "sin_asignar" || !value ? "opacity-100" : "opacity-0"
                  )}
                />
                Sin asignar
              </CommandItem>
              {options.map((option) => (
                <CommandItem key={option} value={option} onSelect={() => handleSelect(option)}>
                  <Check
                    className={cn(
                      "mr-2 h-4 w-4",
                      value === option ? "opacity-100" : "opacity-0"
                    )}
                  />
                  {option}
                </CommandItem>
              ))}
            </CommandGroup>
            {searchValue && !options.some((o) => o.toLowerCase() === searchValue.toLowerCase()) && (
              <CommandGroup>
                <CommandItem value={searchValue} onSelect={() => handleSelect(searchValue)}>
                  <Plus className="mr-2 h-4 w-4" />
                  Crear "{searchValue}"
                </CommandItem>
              </CommandGroup>
            )}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
