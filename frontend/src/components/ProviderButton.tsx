import { useTranslation } from 'components/i18n/Translator';
import { Microsoft } from 'components/icons/Microsoft';

import { Button } from './ui/button';

function capitalizeFirstLetter(string: string) {
  return string.charAt(0).toUpperCase() + string.slice(1);
}

function getProviderName(provider: string) {
  if (provider.startsWith('azure')) {
    return 'Microsoft';
  }
  return capitalizeFirstLetter(provider);
}

function renderProviderIcon(provider: string) {
  if (provider.startsWith('azure')) {
    return <Microsoft />;
  }
  return null;
}

interface ProviderButtonProps {
  provider: string;
  onClick: () => void;
}

const ProviderButton = ({
  provider,
  onClick
}: ProviderButtonProps): JSX.Element => {
  const { t } = useTranslation();
  return (
    <Button type="button" variant="outline" onClick={onClick}>
      {renderProviderIcon(provider.toLowerCase())}
      {t('auth.provider.continue', {
        provider: getProviderName(provider)
      })}
    </Button>
  );
};

export { ProviderButton };
